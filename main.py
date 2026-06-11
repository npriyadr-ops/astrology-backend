import os
import time
import httpx
from datetime import date, time as dt_time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="Vedic CosmicEngine API",
    description="Vedic Astrology calculations and Gemini-powered AI predictions",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

class BirthDetails(BaseModel):
    name: str
    birth_date: date
    birth_time: dt_time
    location: str
    lat: float
    lng: float

def calculate_vedic_coordinates(lat: float, lng: float, birth_date: date, birth_time: dt_time):
    rashis = [
        "Mesha (Aries)", "Vrishabha (Taurus)", "Mithuna (Gemini)", "Karka (Cancer)",
        "Simha (Leo)", "Kanya (Virgo)", "Tula (Libra)", "Vrischika (Scorpio)",
        "Dhanu (Sagittarius)", "Makara (Capricorn)", "Kumbha (Aquarius)", "Meena (Pisces)"
    ]
    nakshatras = [
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha",
        "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Svati", "Vishakha", "Anuradha", "Jyeshtha",
        "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
    ]

    day_score = birth_date.day + birth_date.month * 30 + (birth_date.year % 100)
    time_score = birth_time.hour + (birth_time.minute / 60.0)
    coord_factor = int(abs(lat + lng + day_score + time_score))

    rashi_idx = coord_factor % 12
    nakshatra_idx = coord_factor % 27
    lagna_idx = (coord_factor + 4) % 12

    dasha_lords = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
    current_dasha = dasha_lords[nakshatra_idx % 9]

    return {
        "lagna": rashis[lagna_idx],
        "rashi": rashis[rashi_idx],
        "nakshatra": nakshatras[nakshatra_idx],
        "nakshatra_ruler": dasha_lords[nakshatra_idx % 9],
        "current_dasha": current_dasha
    }

async def generate_gemini_prediction(prompt: str, system_instruction: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": system_instruction}]}
    }
    
    async with httpx.AsyncClient() as client:
        for attempt in range(3):
            try:
                response = await client.post(url, json=payload, timeout=30.0)
                if response.status_code == 200:
                    data = response.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"]
            except Exception:
                time.sleep(2)
                
    raise HTTPException(status_code=502, detail="Stellar pathways are congested. Please execute again.")

@app.get("/")
def read_root():
    return {"status": "Vedic CosmicEngine Online"}

@app.post("/api/v1/vedic/ai-horoscope")
async def generate_vedic_horoscope(details: BirthDetails):
    if not GEMINI_API_KEY:
        return {
            "status": "success",
            "horoscope": "Fallback: Key missing on Render dashboard configuration panels."
        }
    
    try:
        charts = calculate_vedic_coordinates(details.lat, details.lng, details.birth_date, details.birth_time)
        
        system_prompt = (
            "You are an expert Vedic Astrologer (Jyotish Guru). Your voice is deeply mystical, highly encouraging, and empathetic. "
            "Format your predictions clearly into three beautiful sections using Markdown headings: '### 🌟 Soul Pathway', '### 💼 Karma & Career', and '### ⚠️ Cosmic Warning'. "
            "Use authentic Sanskrit terms with brief parenthetical English translations."
        )
        
        user_prompt = (
            f"Generate a personalized daily reading for {details.name}. "
            f"Vedic Chart placements:\n"
            f"- Lagna (Ascendant): {charts['lagna']}\n"
            f"- Rashi (Moon Sign): {charts['rashi']}\n"
            f"- Nakshatra: {charts['nakshatra']}\n"
            f"- Active Vimshottari Dasha: {charts['current_dasha']} Dasha.\n"
        )
        
        prediction = await generate_gemini_prediction(user_prompt, system_prompt)
        
        return {
            "name": details.name,
            "status": "success",
            "vedic_profile": charts,
            "horoscope": prediction
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))