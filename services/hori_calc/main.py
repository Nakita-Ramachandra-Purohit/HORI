from fastapi import FastAPI
from pydantic import BaseModel
app = FastAPI(title="HORI Calculator")

class Inputs(BaseModel):
    temp_c: float | None = None
    aqi: int | None = None
    wind_mps: float | None = None
    precip_mmph: float | None = None

def subscore_temp(t):
    if t is None: return 0
    # simple demo bins
    if t < -5: return 60
    if t < 0: return 40
    if t < 10: return 20
    if t < 25: return 10
    if t < 32: return 30
    return 70

def subscore_aqi(a):
    if a is None: return 0
    return max(0, min(100, (a/200)*100))  # AQI 200 -> 100 risk

def subscore_wind(w):
    if w is None: return 0
    return min(100, w*5)  # very rough demo

def subscore_precip(p):
    if p is None: return 0
    return min(100, p*10)  # rough demo

def band(score):
    return ("Low" if score < 25 else
            "Moderate" if score < 50 else
            "High" if score < 75 else
            "Extreme")

@app.post("/score")
def score(i: Inputs):
    parts = {
        "temp": subscore_temp(i.temp_c),
        "aqi": subscore_aqi(i.aqi),
        "wind": subscore_wind(i.wind_mps),
        "precip": subscore_precip(i.precip_mmph),
    }
    # Weight AQI highest for health focus
    total = 0.5*parts["aqi"] + 0.25*parts["temp"] + 0.15*parts["wind"] + 0.10*parts["precip"]
    top = max(parts, key=parts.get)
    return {
        "hori": round(min(100, total), 1),
        "band": band(total),
        "top_factor": top,
        "parts": parts
    }
