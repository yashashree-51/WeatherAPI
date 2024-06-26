from pydantic import BaseModel

class WeatherResponse(BaseModel):
    city: str
    temperature: float
    humidity: int
    wind_speed: float
    precipitation: float
    feels_like: float
    date: str  
    time: str
