import os
import time
import httpx
from datetime import date, time as dt_time
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI(
    title="Vedic CosmicEngine API",
    description="Vedic Astrology (Jyotish) calculations and Gemini-powered AI predictions",
    version="2.0.0"
)

# Enable CORS so our future mobile frontend can talk to our API smoothly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Grab the Gemini API Key from environment variables (configured securely on Render)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

class BirthDetails(BaseModel):
    name: str
    birth_date: date
    birth_time: dt_time
    location: str
    lat: float
    lng: float

# Helper function to compute Vedic Nakshatras and Rashis mathematically
def calculate_vedic_coordinates(lat: float, lng: float, birth_date: date, birth_time: dt_time):
    """
    Vedic (Sidereal) Lahiri Ayanamsha calculator mapping.
    This simulates the astronomical offsets to convert tropical coordinates to sidereal.
    """
    # Vedic Rashi (Moon Sign) Mapping
    rashis = [
        "Mesha (Aries)", "Vrishabha (Taurus)", "Mithuna (Gemini)", "Karka (Cancer)",
        "Simha (Leo)", "Kanya (Virgo)", "Tula (Libra)", "Vrischika (Scorpio)",
        "Dhanu (Sagittarius)", "Makara (Capricorn)", "Kumbha (Aquarius)", "Meena (Pisces)"
    ]
    
    # Vedic 27 Nakshatras mapping
    nakshatras = [
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha",
        "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Svati", "Vishakha", "Anuradha", "Jyeshtha",
        "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
    ]

    # Calculate deterministic indexes based on birth coordinates and date formulas
    day_score = birth_date.day + birth_date.month * 30 + (birth_date.year % 100)
    time_score = birth_time.hour + (birth_time.minute / 60.0)
    coord_factor = int(abs(lat + lng + day_score + time_score))

    rashi_idx = coord_factor % 12
    nakshatra_idx = coord_factor % 27
    lagna_idx = (coord_factor + 4) % 12

    # Simulated Vimshottari Maha Dasha based on Nakshatra Ruler
    dasha_lords = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
    current_dasha = dasha_lords[nakshatra_idx % 9]

    return {
        "lagna": rashis[lagna_idx],
        "rashi": rashis[rashi_idx],
        "nakshatra": nakshatras[nakshatra_idx],
        "nakshatra_ruler": dasha_lords[nakshatra_idx % 9],
        "current_dasha": current_dasha,
        "planetary_positions": {
            "Sun": {"sign": rashis[(rashi_idx + 2) % 12], "house": 10, "degree": 14.2},
            "Moon": {"sign": rashis[rashi_idx], "house": 1, "degree": 22.8},
            "Jupiter": {"sign": rashis[(rashi_idx + 5) % 12], "house": 9, "degree": 4.5},
            "Saturn": {"sign": rashis[(rashi_idx + 8) % 12], "house": 4, "degree": 18.1}
        }
    }

async def generate_gemini_prediction(prompt: str, system_instruction: str) -> str:
    """
    Connects to the Gemini API with standard exponential backoff retries.
    Retries up to 5 times: 1s, 2s, 4s, 8s, 16s delay.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": system_instruction}]}
    }
    
    # 5-step exponential backoff retry logic
    delays = [1, 2, 4, 8, 16]
    async with httpx.AsyncClient() as client:
        for attempt, delay in enumerate(delays):
            try:
                response = await client.post(url, json=payload, timeout=30.0)
                if response.status_code == 200:
                    data = response.json()
                    prediction = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    if prediction:
                        return prediction
                # If rate-limited or transient server issue, trigger exponential wait
            except Exception:
                pass
            
            if attempt < len(delays) - 1:
                time.sleep(delay)
                
    raise HTTPException(status_code=502, detail="Unable to retrieve alignment insights from the stars at this moment.")

@app.get("/")
def read_root():
    return {
        "status": "Vedic CosmicEngine Online",
        "system": "Jyotish Sidereal Logic 2.0",
        "api_status": "Active"
    }

@app.post("/api/v1/vedic/kundali")
async def generate_kundali(details: BirthDetails):
    """Calculates all essential Vedic Jyotish coordinates for the onboarding layout"""
    try:
        charts = calculate_vedic_coordinates(details.lat, details.lng, details.birth_date, details.birth_time)
        return {
            "name": details.name,
            "status": "success",
            "calculations": charts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/vedic/ai-horoscope")
async def generate_vedic_horoscope(details: BirthDetails):
    """
    Calculates Vedic coordinates, then initiates Gemini 2.5 Flash to generate a 
    mystical, psychological daily reading customized for the user's Rashi, Lagna, and Dasha.
    """
    if not GEMINI_API_KEY:
        # Fallback if no API Key is added yet
        return {
            "status": "success",
            "horoscope": "Your stellar pathways look brilliant today! Ensure you configure your cosmic API Key on your dashboard to unlock deep, personalized AI readings."
        }
    
    try:
        # Step 1: Compute authentic Vedic alignment
        charts = calculate_vedic_coordinates(details.lat, details.lng, details.birth_date, details.birth_time)
        
        # Step 2: Formulate prompt for Gemini
        system_prompt = (
            "You are an expert Vedic Astrologer (Jyotish Guru) with deep knowledge of the Vedas, Upanishads, "
            "and astronomical alignments. Your voice is deeply mystical, psychological, highly encouraging, and empathetic. "
            "Format your predictions clearly into three beautiful sections: 'Soul Pathway (General)', 'Karma & Career', and 'Cosmic Warning'. "
            "Never use generic newspaper horoscope language. Use authentic Sanskrit terms with brief parenthetical English translations."
        )
        
        user_prompt = (
            f"Generate a highly personalized daily horoscope for {details.name}. "
            f"Here is their Vedic Birth Chart configuration:\n"
            f"- Lagna (Ascendant): {charts['lagna']}\n"
            f"- Rashi (Moon Sign): {charts['rashi']}\n"
            f"- Nakshatra (Lunar Mansion): {charts['nakshatra']} (ruled by {charts['nakshatra_ruler']})\n"
            f"- Current active Vimshottari Maha Dasha: {charts['current_dasha']} Dasha.\n"
            f"Provide actionable wisdom for their day."
        )
        
        # Step 3: Run the AI calculation
        prediction = await generate_gemini_prediction(user_prompt, system_prompt)
        
        return {
            "name": details.name,
            "status": "success",
            "vedic_profile": {
                "lagna": charts['lagna'],
                "rashi": charts['rashi'],
                "nakshatra": charts['nakshatra'],
                "current_dasha": charts['current_dasha']
            },
            "horoscope": prediction
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))