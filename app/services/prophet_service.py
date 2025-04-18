from prophet import Prophet
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Tuple, List
from ..database.db import Database

logger = logging.getLogger("prophet_service")

class ProphetService:
    def __init__(self):
        self.db = Database()

    def prepare_data(self, topic, platform=None):
        """Prepare data for Prophet model."""
        try:
            # Get aggregated daily data
            daily_data = self.db.get_aggregated_daily_data(topic, platform)
            
            logger.info(f"Preparing data for Prophet: {len(daily_data)} data points")
            
            # Debug the structure of the first item to understand the issue
            if daily_data and len(daily_data) > 0:
                logger.info(f"Data structure: {daily_data[0]}")
            
            # Create proper DataFrame structure for Prophet
            # Fix: Handle both possible structures from MongoDB
            df = pd.DataFrame([
                {'ds': d['ds'] if 'ds' in d else d.get('_id', {}).get('date'),
                 'y': d['y']}
                for d in daily_data
            ])
            
            # Ensure ds is in datetime format
            if 'ds' in df.columns and df['ds'].dtype == 'object':
                df['ds'] = pd.to_datetime(df['ds'])
                
            return df
        except Exception as e:
            logger.error(f"Error preparing data: {str(e)}")
            raise

    def make_forecast(self, topic, platform=None, periods=7, frequency='D'):
        """Generate a forecast for the given topic and platform."""
        try:
            logger.info(f"Making forecast for topic: {topic}, platform: {platform}, periods: {periods}")
            
            # If we don't have enough data, use a different approach
            historical_data = self.db.get_historical_data(topic, platform)
            
            if len(historical_data) < 2:
                logger.warning("Not enough historical data points for standard forecasting. Using simplified approach.")
                return self.make_simple_forecast(historical_data, periods)
            
            # Prepare data for Prophet
            df = self.prepare_data(topic, platform)
            
            if df.empty or len(df) < 2:
                logger.warning(f"Insufficient data for forecast: only {len(df) if not df.empty else 0} points")
                return self.make_simple_forecast(historical_data, periods)
            
            # Initialize and fit Prophet model
            model = Prophet(
                daily_seasonality=False,
                weekly_seasonality=True if len(df) >= 7 else False,
                yearly_seasonality=False,
                seasonality_mode='additive',
                interval_width=0.95
            )
            
            model.fit(df)
            
            # Create future dataframe
            future = model.make_future_dataframe(periods=periods, freq=frequency)
            forecast = model.predict(future)
            
            # Extract forecast components
            forecast_dates = forecast['ds'].tail(periods).dt.strftime('%Y-%m-%d').tolist()
            forecast_values = forecast['yhat'].tail(periods).tolist()
            lower_bounds = forecast['yhat_lower'].tail(periods).tolist()
            upper_bounds = forecast['yhat_upper'].tail(periods).tolist()
            
            # Extract historical data
            historical_dates = df['ds'].dt.strftime('%Y-%m-%d').tolist()
            historical_values = df['y'].tolist()
            
            logger.info(f"Forecast generated successfully with {len(forecast_dates)} points")
            
            return (
                forecast_dates,
                forecast_values,
                lower_bounds,
                upper_bounds,
                historical_dates,
                historical_values
            )
            
        except Exception as e:
            logger.error(f"Error generating forecast: {str(e)}")
            raise

    def make_simple_forecast(self, historical_data, periods=7):
        """Generate a simple forecast when we don't have enough data for Prophet."""
        try:
            # Extract the latest value
            if not historical_data:
                return [], [], [], [], [], []
                
            latest_value = historical_data[-1]['value']
            latest_date = datetime.fromisoformat(historical_data[-1]['timestamp'].replace('Z', '+00:00'))
            
            # Generate forecast dates
            forecast_dates = [(latest_date + pd.Timedelta(days=i+1)).strftime('%Y-%m-%d') 
                             for i in range(periods)]
            
            # Simple forecast: use the latest value with small variations
            forecast_values = [latest_value for _ in range(periods)]
            
            # Add 10% margin for upper/lower bounds
            lower_bounds = [0.9 * v for v in forecast_values]
            upper_bounds = [1.1 * v for v in forecast_values]
            
            # Historical data
            historical_dates = [datetime.fromisoformat(d['timestamp'].replace('Z', '+00:00')).strftime('%Y-%m-%d') 
                              for d in historical_data]
            historical_values = [d['value'] for d in historical_data]
            
            logger.info(f"Simple forecast generated with {len(forecast_dates)} points")
            
            return (
                forecast_dates,
                forecast_values,
                lower_bounds,
                upper_bounds,
                historical_dates,
                historical_values
            )
        except Exception as e:
            logger.error(f"Error generating simple forecast: {str(e)}")
            raise 