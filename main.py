from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import date, time

app = FastAPI(
    title="CosmicEngine API", 
    description="Free-tier backend calculations for our Astrology App",
    version="1.0.0"
)

class BirthDetails(BaseModel):
    name: str
    birth_date: date
    birth_time: time
    location: str
    lat: float
    lng: float

@app.get("/")
def read_root():
    return {
        "status": "Cosmic Engine Online", 
        "environment": "Local Development"
    }

@app.post("/api/v1/natal-chart")
async def generate_natal_chart(details: BirthDetails):
    try:
        simulated_chart_data = {
            "sun": {"sign": "Leo", "house": 11, "degree": 14.5},
            "moon": {"sign": "Scorpio", "house": 3, "degree": 22.1},
            "ascendant": {"sign": "Libra", "degree": 4.2}
        }
        return {
            "user": details.name,
            "status": "success",
            "data": simulated_chart_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))