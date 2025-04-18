from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class TimeSeriesData(BaseModel):
    topic: str
    platform: str
    timestamp: datetime
    value: float
    metadata: Dict[str, Any] = {}

class ForecastRequest(BaseModel):
    topic: str
    platform: Optional[str] = None
    periods: int = 7
    frequency: str = "D"
    include_history: bool = True

class ForecastResponse(BaseModel):
    topic: str
    platform: Optional[str] = None
    forecast_dates: List[str]
    forecast_values: List[float]
    lower_bounds: List[float]
    upper_bounds: List[float]
    historical_dates: Optional[List[str]] = None
    historical_values: Optional[List[float]] = None 