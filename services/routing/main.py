from fastapi import FastAPI
from pydantic import BaseModel
from math import radians, cos, sin, asin, sqrt
app = FastAPI(title="Routing Stub")

class Point(BaseModel):
    lat: float
    lon: float

class RouteReq(BaseModel):
    origin: Point
    dest: Point
    depart_iso: str
    speed_kmh: float = 60.0  # demo default
    samples: int = 20        # segments along route

def haversine_km(a: Point, b: Point):
    lon1, lat1, lon2, lat2 = map(radians, [a.lon, a.lat, b.lon, b.lat])
    dlon, dlat = lon2 - lon1, lat2 - lat1
    h = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return 2 * 6371 * asin(sqrt(h))

@app.post("/route")
def route(r: RouteReq):
    import datetime as dt, json
    depart = dt.datetime.fromisoformat(r.depart_iso.replace("Z","+00:00"))
    total_km = haversine_km(r.origin, r.dest)
    total_h = total_km / r.speed_kmh if r.speed_kmh > 0 else 1
    # Interpolate lat/lon
    lats = [r.origin.lat + (r.dest.lat - r.origin.lat)*i/r.samples for i in range(r.samples+1)]
    lons = [r.origin.lon + (r.dest.lon - r.origin.lon)*i/r.samples for i in range(r.samples+1)]
    # Simple timestamps
    times = [ (depart + dt.timedelta(hours=total_h*i/r.samples)).isoformat() for i in range(r.samples+1)]
    # Very simple polyline surrogate (list of points)
    points = [{"lat": lats[i], "lon": lons[i], "t": times[i]} for i in range(r.samples+1)]
    return {
        "distance_km": round(total_km, 2),
        "duration_min": int(total_h*60),
        "points": points
    }
