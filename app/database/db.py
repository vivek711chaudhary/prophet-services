import logging
from pymongo import MongoClient
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path to find root config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("prophet_service.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("prophet_db")

class Database:
    def __init__(self):
        try:
            logger.info(f"Attempting to connect to MongoDB at: {settings.MONGODB_URI}")
            
            self.client = MongoClient(settings.MONGODB_URI)
            
            # Explicitly use the existing database
            self.db = self.client.prophet_db  # Use existing database
            self.engagements = self.db.engagements  # Use existing collection
            
            # Log database and collection names
            logger.info(f"Using database: prophet_db and collection: engagements")
            
            # Test the connection
            self.client.admin.command('ping')
            
            # Count documents to verify connection to the collection
            doc_count = self.engagements.count_documents({})
            logger.info(f"MongoDB connection successful. Found {doc_count} documents in engagements collection")
        except Exception as e:
            logger.error(f"MongoDB connection error: {str(e)}")
            raise

    def store_engagement_data(self, data):
        """Store engagement data in MongoDB."""
        try:
            logger.info(f"Storing engagement data for topic: {data.get('topic')}, platform: {data.get('platform')}")
            
            # Ensure timestamp is a datetime object
            if isinstance(data.get('timestamp'), str):
                data['timestamp'] = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            
            # Add created_at field
            data['created_at'] = datetime.utcnow()
            
            # Insert into MongoDB
            result = self.engagements.insert_one(data)
            
            logger.info(f"Data stored successfully with ID: {result.inserted_id}")
            return result.inserted_id
        except Exception as e:
            logger.error(f"Error storing engagement data: {str(e)}")
            logger.error(f"Data that failed: {data}")
            raise

    def get_historical_data(self, topic, platform=None):
        """Get historical engagement data for a topic."""
        try:
            logger.info(f"Retrieving historical data for topic: {topic}, platform: {platform}")
            
            # Build query
            query = {"topic": topic}
            if platform:
                query["platform"] = platform
                
            # Execute query and convert to list
            results = list(self.engagements.find(
                query, 
                {"_id": 0}
            ).sort("timestamp", 1))
            
            logger.info(f"Retrieved {len(results)} historical data points")
            
            # Convert datetime objects to ISO format strings for JSON serialization
            for result in results:
                if isinstance(result.get('timestamp'), datetime):
                    result['timestamp'] = result['timestamp'].isoformat()
                if isinstance(result.get('created_at'), datetime):
                    result['created_at'] = result['created_at'].isoformat()
                    
            return results
        except Exception as e:
            logger.error(f"Error retrieving historical data: {str(e)}")
            raise

    def get_aggregated_daily_data(self, topic, platform=None):
        """Get daily aggregated engagement data for Prophet."""
        try:
            logger.info(f"Retrieving aggregated daily data for topic: {topic}, platform: {platform}")
            
            # Build match stage
            match_stage = {"topic": topic}
            if platform:
                match_stage["platform"] = platform
                
            # Build pipeline
            pipeline = [
                {"$match": match_stage},
                {"$group": {
                    "_id": {
                        "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}}
                    },
                    "y": {"$sum": "$value"}
                }},
                {"$sort": {"_id.date": 1}},
                {"$project": {
                    "_id": 0,
                    "ds": "$_id.date",
                    "y": 1
                }}
            ]
            
            # Execute aggregation
            results = list(self.engagements.aggregate(pipeline))
            
            logger.info(f"Retrieved {len(results)} aggregated data points")
            return results
        except Exception as e:
            logger.error(f"Error retrieving aggregated data: {str(e)}")
            raise 

    def get_recent_platform_average(self, topic, platform, days=7):
        """Get average engagement for a topic and platform over recent days."""
        try:
            topic = topic.lower()  # Normalize topic case
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Build query
            query = {
                "topic": topic,
                "platform": platform,
                "timestamp": {"$gte": cutoff_date}
            }
            
            # Execute query
            results = list(self.engagements.find(query))
            
            if not results:
                logger.info(f"No recent data for {topic}/{platform}")
                return 0
            
            # Calculate average
            total = sum(doc.get("value", 0) for doc in results)
            avg = total / len(results)
            
            logger.info(f"Average engagement for {topic}/{platform}: {avg} (from {len(results)} records)")
            return avg
        except Exception as e:
            logger.error(f"Error calculating recent average: {str(e)}")
            return 0

    def get_search_volume(self, topic, days=30):
        """Get search volume for a topic over time."""
        try:
            topic = topic.lower()  # Normalize topic case
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Build pipeline for daily aggregation
            pipeline = [
                {"$match": {
                    "topic": topic,
                    "platform": "search_volume",
                    "timestamp": {"$gte": cutoff_date}
                }},
                {"$group": {
                    "_id": {
                        "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}}
                    },
                    "count": {"$sum": "$value"}
                }},
                {"$sort": {"_id.date": 1}}
            ]
            
            # Execute aggregation
            results = list(self.engagements.aggregate(pipeline))
            
            # Format results
            volume_data = [
                {"date": item["_id"]["date"], "count": item["count"]}
                for item in results
            ]
            
            logger.info(f"Retrieved search volume data for {topic}: {len(volume_data)} days")
            return volume_data
        except Exception as e:
            logger.error(f"Error retrieving search volume: {str(e)}")
            raise 