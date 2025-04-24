# Prophet Forecasting Service

A FastAPI-based microservice for time series forecasting using Facebook Prophet. This service provides APIs for storing engagement data and generating forecasts for various topics across different platforms.

## Overview

The Prophet Forecasting Service is designed to:

1. Store engagement data for topics across various platforms (Twitter, Reddit, News, etc.)
2. Generate time series forecasts using Facebook Prophet
3. Provide historical engagement data analysis

## Features

- Store engagement data with metadata
- Track search volume for topics
- Generate forecasts with confidence intervals
- Support for multiple platforms and topics
- Daily data aggregation for better forecasting
- MongoDB database integration
- Fully containerized with Docker
- Deployment support for GCP Cloud Run and App Engine

## Tech Stack

- **Framework**: FastAPI
- **Forecasting Library**: Facebook Prophet
- **Database**: MongoDB
- **Container**: Docker
- **Deployment**: GCP Cloud Run / App Engine

## API Endpoints

### Data Storage

- **POST** `/api/v1/store-engagement`: Store individual engagement data points
- **POST** `/api/v1/store-platform-engagements`: Store multiple engagement metrics from platforms

### Forecasting

- **POST** `/api/v1/forecast`: Generate forecast for a specific topic/platform

### Analytics

- **GET** `/api/v1/topics/{topic}/history`: Get historical data for a topic
- **GET** `/api/v1/health-check`: Service health check

## Quick Start

### Prerequisites

- Python 3.9+
- MongoDB instance (local or cloud)
- Docker (optional)

### Local Development

1. Clone the repository
   ```bash
   git clone <repository-url>
   cd prophet-services
   ```

2. Set up environment variables (create a `.env` file)
   ```
   MONGODB_URI=mongodb+srv://username:password@your-mongodb-cluster/
   MODEL_CACHE_DIR=cache
   DEBUG=True
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Run the service
   ```bash
   python run.py
   ```

5. The API will be available at http://localhost:8000

### Docker

```bash
# Build the Docker image
docker build -t prophet-service:latest .

# Run the container
docker run -p 8000:8000 -e MONGODB_URI="your-mongodb-connection-string" prophet-service:latest
```

## Deployment

See [deploy.md](deploy.md) for detailed deployment instructions for Google Cloud Platform.

### Current Deployment

The service is currently deployed on a Google Cloud VM instance and can be accessed at:

```
PROPHET_SERVICE_URL = "http://34.45.252.228:8000"
```

Use this URL for API calls from your client applications.

## Project Structure

```
prophet-services/
├── app/
│   ├── database/
│   │   └── db.py              # MongoDB connection and data operations
│   ├── models/
│   │   └── time_series.py     # Pydantic models for data validation
│   ├── routes/
│   │   └── forecast_routes.py # API route handlers
│   ├── services/
│   │   └── prophet_service.py # Prophet forecasting implementation
├── main.py                    # FastAPI application entrypoint
├── run.py                     # Development server runner
├── config.py                  # Application configuration
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker configuration
├── app.yaml                   # App Engine configuration
├── cloudbuild.yaml            # Cloud Build configuration
└── deploy.md                  # Deployment documentation
```

## Configuration

The application uses environment variables for configuration:

- `MONGODB_URI`: MongoDB connection string
- `MODEL_CACHE_DIR`: Directory for storing Prophet model cache
- `DEBUG`: Enable/disable debug mode

## Usage Examples

### Storing Engagement Data

```python
import requests
import json

url = "http://localhost:8000/api/v1/store-engagement"
data = {
    "topic": "machine_learning",
    "platform": "twitter",
    "timestamp": "2023-05-01T12:00:00Z",
    "value": 145.5,
    "metadata": {
        "result_count": 450,
        "query": "machine learning"
    }
}

response = requests.post(url, json=data)
print(response.json())
```

### Generating a Forecast

```python
import requests
import json

url = "http://localhost:8000/api/v1/forecast"
data = {
    "topic": "machine_learning",
    "platform": "twitter",
    "periods": 14,
    "frequency": "D",
    "include_history": True
}

response = requests.post(url, json=data)
forecast = response.json()
```

## License

[Your License Information]

## Contact

[Your Contact Information] 