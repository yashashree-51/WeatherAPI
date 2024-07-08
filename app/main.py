import os
import pycountry
import requests
from fastapi import FastAPI, HTTPException, Query
from datetime import datetime
from pytz import timezone, utc
from timezonefinder import TimezoneFinder
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        country_code = weather_data['sys'].get('country', 'Unknown')
        country = pycountry.countries.get(alpha_2=country_code).name if country_code != 'Unknown' else 'Unknown'
        city = weather_data.get('name', 'Unknown')
        temperature = weather_data['main']['temp']
        humidity = weather_data['main']['humidity']
        wind_speed = weather_data['wind']['speed']
        feels_like = weather_data['main']['feels_like']

        # Handling possible absence of rain information
        print(weather_data)
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
        time = local_time.strftime('%H:%M')

        return {
            "country": country,
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
@app.get("/weather")
async def get_weather(lat: float = Query(..., description="Latitude for which to retrieve weather"),
                      lon: float = Query(..., description="Longitude for which to retrieve weather")):
    try:
        data = get_weather_data(lat=lat, lon=lon)
        return data
    except HTTPException as e:
        raise e
