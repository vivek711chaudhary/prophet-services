from fastapi import APIRouter, HTTPException, Request
import logging
import traceback
from ..models.time_series import TimeSeriesData, ForecastRequest, ForecastResponse
from ..services.prophet_service import ProphetService
from ..database.db import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("prophet_service.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("forecast_routes")

router = APIRouter()
prophet_service = ProphetService()
db = Database()

@router.post("/store-engagement")
async def store_engagement(data: TimeSeriesData, request: Request):
    try:
        client_host = request.client.host
        logger.info(f"Received store-engagement request from {client_host} for topic: {data.topic}")
        
        # Store the raw data first
        data_dict = data.dict()
        logger.info(f"Data to store: {data_dict}")
        
        # Store in database
        db.store_engagement_data(data_dict)
        
        # Track search volume - increment search count for this topic
        # This creates a separate record to track searches
        search_data = {
            "topic": data.topic.lower(),  # Normalize topic to lowercase
            "platform": "search_volume",  # Special platform identifier for searches
            "timestamp": data.timestamp,
            "value": 1,  # Each API call counts as 1 search
            "metadata": {
                "source_ip": client_host,
                "query_platform": data.platform
            }
        }
        db.store_engagement_data(search_data)
        
        logger.info(f"Data successfully stored for topic: {data.topic}")
        return {"status": "success", "message": "Data stored successfully"}
    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Error storing engagement data: {str(e)}\n{error_trace}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/store-platform-engagements")
async def store_platform_engagements(request: Request):
    """Store detailed engagement metrics from all platforms."""
    try:
        data = await request.json()
        client_host = request.client.host
        
        if not data or not isinstance(data, dict) or "results" not in data:
            raise HTTPException(status_code=400, detail="Invalid data format")
        
        results = data.get("results", [])
        topic = data.get("topic", "unknown").lower()
        
        logger.info(f"Received platform engagements for topic: {topic} with {len(results)} items")
        
        # Group by platform
        engagements_by_platform = {}
        for item in results:
            platform = item.get("platform")
            if not platform:
                continue
                
            if platform not in engagements_by_platform:
                engagements_by_platform[platform] = {
                    "items": [],
                    "total_likes": 0,
                    "total_shares": 0,
                    "total_comments": 0
                }
                
            # Add to items list
            engagements_by_platform[platform]["items"].append(item)
            
            # Sum engagement metrics
            engagement = item.get("engagement", {})
            engagements_by_platform[platform]["total_likes"] += engagement.get("likes", 0)
            engagements_by_platform[platform]["total_shares"] += engagement.get("shares", 0)
            engagements_by_platform[platform]["total_comments"] += engagement.get("comments", 0)
        
        # Store aggregate engagement for each platform
        timestamp = data.get("timestamp") or results[0].get("timestamp") if results else None
        
        stored_platforms = []
        for platform, metrics in engagements_by_platform.items():
            # Calculate weighted engagement score
            engagement_score = (
                metrics["total_likes"] + 
                (metrics["total_shares"] * 2) + 
                (metrics["total_comments"] * 1.5)
            )
            
            # Store platform-specific engagement data
            platform_data = {
                "topic": topic,
                "platform": platform,
                "timestamp": timestamp,
                "value": engagement_score,
                "metadata": {
                    "items_count": len(metrics["items"]),
                    "likes": metrics["total_likes"],
                    "shares": metrics["total_shares"],
                    "comments": metrics["total_comments"],
                    "api_status": data.get("stats", {}).get("platform_status", {}).get(platform, "unknown")
                }
            }
            
            # Handle platform failures gracefully
            platform_status = data.get("stats", {}).get("platform_status", {}).get(platform)
            if platform_status != "success":
                # If platform failed but we're still tracking the search,
                # use a reasonable fallback value based on historical data
                try:
                    historical = db.get_recent_platform_average(topic, platform, days=7)
                    if historical > 0:
                        platform_data["value"] = historical
                        platform_data["metadata"]["estimated"] = True
                        logger.info(f"Using estimated engagement for {platform}: {historical}")
                except Exception as e:
                    logger.error(f"Error getting historical data: {str(e)}")
            
            db.store_engagement_data(platform_data)
            stored_platforms.append(platform)
        
        return {
            "status": "success", 
            "message": f"Stored engagement data for {len(stored_platforms)} platforms",
            "platforms": stored_platforms
        }
    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Error storing platform engagements: {str(e)}\n{error_trace}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/forecast", response_model=ForecastResponse)
async def get_forecast(request: ForecastRequest):
    try:
        logger.info(f"Received forecast request for topic: {request.topic}, platform: {request.platform}")
        
        # Check if we have historical data
        historical_data = db.get_historical_data(request.topic, request.platform)
        if not historical_data:
            logger.warning(f"No historical data found for topic: {request.topic}, platform: {request.platform}")
            raise HTTPException(status_code=404, detail="No historical data found for this topic/platform")
        
        logger.info(f"Found {len(historical_data)} historical data points, generating forecast")
            
        (
            forecast_dates,
            forecast_values,
            lower_bounds,
            upper_bounds,
            historical_dates,
            historical_values
        ) = prophet_service.make_forecast(
            topic=request.topic,
            platform=request.platform,
            periods=request.periods,
            frequency=request.frequency
        )

        response = ForecastResponse(
            topic=request.topic,
            platform=request.platform,
            forecast_dates=forecast_dates,
            forecast_values=forecast_values,
            lower_bounds=lower_bounds,
            upper_bounds=upper_bounds,
            historical_dates=historical_dates if request.include_history else None,
            historical_values=historical_values if request.include_history else None
        )

        logger.info(f"Successfully generated forecast for topic: {request.topic}")
        return response
    except HTTPException:
        raise
    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Error generating forecast: {str(e)}\n{error_trace}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/topics/{topic}/history")
async def get_topic_history(topic: str, platform: str = None):
    try:
        logger.info(f"Received history request for topic: {topic}, platform: {platform}")
        
        data = db.get_historical_data(topic, platform)
        
        if not data:
            logger.warning(f"No historical data found for topic: {topic}, platform: {platform}")
            return {"topic": topic, "platform": platform, "data": [], "message": "No data found"}
            
        logger.info(f"Returning {len(data)} historical data points")
        return {"topic": topic, "platform": platform, "data": data}
    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Error retrieving topic history: {str(e)}\n{error_trace}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health-check")
async def health_check():
    """Check service health and data status."""
    try:
        # Check MongoDB connection
        db.client.admin.command('ping')
        
        # Check database collections
        collection_names = db.db.list_collection_names()
        
        # Count records by topic
        topic_counts = {}
        try:
            pipeline = [
                {"$group": {"_id": "$topic", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            topics = list(db.engagements.aggregate(pipeline))
            for topic in topics:
                topic_counts[topic["_id"]] = topic["count"]
        except Exception as e:
            logger.error(f"Error counting topics: {str(e)}")
            
        # Count records by platform
        platform_counts = {}
        try:
            pipeline = [
                {"$group": {"_id": "$platform", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            platforms = list(db.engagements.aggregate(pipeline))
            for platform in platforms:
                platform_counts[platform["_id"]] = platform["count"]
        except Exception as e:
            logger.error(f"Error counting platforms: {str(e)}")
            
        return {
            "status": "healthy",
            "database": "connected",
            "collections": collection_names,
            "topics": topic_counts,
            "platforms": platform_counts
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}") 