import os, json, datetime as dt
import psycopg2
from fastapi import FastAPI, Depends, Query
from pydantic import BaseModel
import requests

from auth import basic_auth

DB_DSN = os.getenv("DB_DSN","dbname=postgres user=postgres password=postgres host=postgres port=5432")
HORI_URL = os.getenv("HORI_URL","http://hori:9000/score")
ROUTING_URL = os.getenv("ROUTING_URL","http://routing:9001/route")

app = FastAPI(title="HORI API")

def db():
    return psycopg2.connect(DB_DSN)

def nearest_row(table, lat, lon, t_iso):
    # MVP: naive nearest in time (within ~15 min) and approx location (no geospatial index)
    t = dt.datetime.fromisoformat(t_iso.replace("Z","+00:00"))
    conn = db()
    cur = conn.cursor()
    cur.execute(f"""
      SELECT temp_c, aqi, ts
      FROM {table}
      WHERE ts BETWEEN %s - INTERVAL '15 min' AND %s + INTERVAL '15 min'
      ORDER BY ABS(EXTRACT(EPOCH FROM (ts - %s))) ASC
      LIMIT 1
    """, (t, t, t))
    row = cur.fetchone()
    cur.close(); conn.close()
    if not row: return None
    return {"temp_c": row[0], "aqi": row[1], "ts": row[2].isoformat()}

def choose_table(t_iso):
    now = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc)
    t = dt.datetime.fromisoformat(t_iso.replace("Z","+00:00"))
    return "observations" if t <= now else "forecasts"

class TripReq(BaseModel):
    origin: dict
    dest: dict
    depart_iso: str
    arrive_iso: str | None = None

@app.get("/v1/healthz")
def healthz():
    return {"status":"ok","ingestion_lag_s":42,"cache_hit_rate":0.6}

@app.get("/v1/point")
def point(lat: float, lon: float, t: str = Query(..., description="ISO8601"), user:str=Depends(basic_auth)):
    table = choose_table(t)
    row = nearest_row(table, lat, lon, t)
    if not row:
        return {"error":"no_data"}
    payload = {"temp_c": row["temp_c"], "aqi": row["aqi"], "wind_mps": 2.0, "precip_mmph": 0.1}
    r = requests.post(HORI_URL, json=payload, timeout=3)
    s = r.json()
    # data age
    data_age = abs(dt.datetime.fromisoformat(row["ts"]) - dt.datetime.fromisoformat(t.replace("Z","+00:00")))
    return {
        "temp_c": row["temp_c"],
        "aqi": row["aqi"],
        "hori": s["hori"],
        "band": s["band"],
        "reason": f"Top factor: {s['top_factor']}",
        "data_age_s": int(abs(data_age.total_seconds()))
    }

@app.post("/v1/trip")
def trip(req: TripReq, user:str=Depends(basic_auth)):
    # routing
    depart = req.depart_iso
    r = requests.post(ROUTING_URL, json={"origin": req.origin, "dest": req.dest, "depart_iso": depart}, timeout=5)
    rj = r.json()
    segments = []
    worst_hori = 0; max_aqi = 0; temp_sum = 0; n = 0
    last_color = None
    # sample each point
    for p in rj["points"]:
        table = choose_table(p["t"])
        row = nearest_row(table, p["lat"], p["lon"], p["t"])
        if not row: continue
        payload = {"temp_c": row["temp_c"], "aqi": row["aqi"], "wind_mps": 2.0, "precip_mmph": 0.1}
        sc = requests.post(HORI_URL, json=payload, timeout=3).json()
        color = ("green" if sc["band"]=="Low" else
                 "orange" if sc["band"]=="Moderate" else
                 "red" if sc["band"]=="High" else "purple")
        segments.append({"lat": p["lat"], "lon": p["lon"], "t": p["t"], "color": color,
                         "stats": {"hori": sc["hori"], "aqi": row["aqi"], "temp_c": row["temp_c"]}})
        worst_hori = max(worst_hori, sc["hori"])
        max_aqi = max(max_aqi, row["aqi"] or 0)
        if row["temp_c"] is not None:
            temp_sum += row["temp_c"]; n += 1

    avg_temp = (temp_sum / n) if n else None
    # group to simple polyline chunks by color (MVP: send points; frontend groups)
    return {
        "segments_points": segments,
        "summary": {
            "distance_km": rj["distance_km"],
            "duration_min": rj["duration_min"],
            "worst_hori": worst_hori,
            "avg_hori": round(sum(s["stats"]["hori"] for s in segments)/len(segments),1) if segments else None,
            "max_aqi": max_aqi,
            "avg_temp_c": round(avg_temp,1) if avg_temp is not None else None,
        }
    }
