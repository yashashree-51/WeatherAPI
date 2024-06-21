import os
import requests
from fastapi import FastAPI, HTTPException, Query
from datetime import datetime
from pytz import timezone, utc
from timezonefinder import TimezoneFinder
from models import WeatherResponse
from dotenv import load_dotenv

app = FastAPI()

load_dotenv()


api_key = os.getenv('OPENWEATHERMAP_API_KEY')


tf = TimezoneFinder()

# Function to fetch weather data from OpenWeatherMap API
def get_weather_data(lat: float, lon: float) -> dict:
    base_url = 'https://api.openweathermap.org/data/2.5/weather'
    params = {
        'units': 'metric',  # Units in Celsius
        'appid': api_key,
        'lat': lat,
        'lon': lon
    }

    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        weather_data = response.json()
        
        # Extract weather details
        city = weather_data.get('name', 'Unknown')
        temperature = weather_data['main']['temp']
        humidity = weather_data['main']['humidity']
        wind_speed = weather_data['wind']['speed']
        feels_like = weather_data['main']['feels_like']

        # Handling possible absence of rain information
        precipitation = weather_data.get('rain', {}).get('1h', 0.0) if 'rain' in weather_data else 0.0
        
        # Convert UTC time to local time using timezonefinder
        utc_time = datetime.utcfromtimestamp(weather_data['dt'])
        utc_time = utc.localize(utc_time)  # Make the UTC time timezone-aware
        
        # Find the timezone from latitude and longitude
        try:
            tz_name = tf.timezone_at(lat=lat, lng=lon)
            if not tz_name:
                raise HTTPException(status_code=400, detail="Timezone not found for the given coordinates")
            target_timezone = timezone(tz_name)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        local_time = utc_time.astimezone(target_timezone)
        
        date = local_time.strftime('%Y-%m-%d')
        time = local_time.strftime('%H:%M:%S %Z%z')

        return {
            "city": city,
            "temperature": temperature,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "precipitation": precipitation,
            "feels_like": feels_like,
            "date": date,  
            "time": time   
        }
    elif response.status_code == 404:
        raise HTTPException(status_code=404, detail="Location not found")
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch weather data")

# GET endpoint 
@app.get("/weather", response_model=WeatherResponse)
async def get_weather(lat: float = Query(..., description="Latitude for which to retrieve weather"),
                      lon: float = Query(..., description="Longitude for which to retrieve weather")):
    try:
        data = get_weather_data(lat=lat, lon=lon)
        return WeatherResponse(**data)
    except HTTPException as e:
        raise e
