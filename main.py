import os
import json
import urllib.request
import urllib.error
from datetime import date, time as dt_time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="Vedic CosmicEngine API",
    description="Vedic Astrology calculations and Gemini-powered AI predictions",
    version="2.2.0"
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

def generate_gemini_prediction_native(prompt: str, system_instruction: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
     "contents": [{"parts": [{"text": prompt}]}],
     "system_instruction": {"parts": [{"text": system_instruction}]}
 }
    
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, 
        data=data, 
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30.0) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return res_data["candidates"][0]["content"]["parts"][0]["text"]
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        raise HTTPException(status_code=502, detail=f"API Error: {err_msg}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Stellar pathways are congested: {str(e)}")

@app.get("/")
def read_root():
    return {"status": "Vedic CosmicEngine Online"}

@app.post("/api/v1/vedic/ai-horoscope")
def generate_vedic_horoscope(details: BirthDetails):
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
        
        prediction = generate_gemini_prediction_native(user_prompt, system_prompt)
        
        return {
            "name": details.name,
            "status": "success",
            "vedic_profile": charts,
            "horoscope": prediction
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
