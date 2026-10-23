"""Institutional Food Wastage and Rapid Distribution Network (core API).

Cafeterias post surplus food; NGO drivers within 10 km can claim it;
handover is confirmed with a one-time password (OTP).
Storage is in-memory here so the CI/CD pipeline needs no database.
In the full project this layer is PostgreSQL/PostGIS.
"""
import math
import secrets
from typing import Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

VERSION = "v1"  # change to "v2", push, and re-run the pipeline for the 2nd-run demo
RADIUS_KM = 10.0

app = FastAPI(title="Food Rescue Network API", version=VERSION)

SURPLUS: Dict[int, dict] = {}
_counter = {"next": 1}


class SurplusIn(BaseModel):
    cafeteria: str
    item: str
    quantity_kg: float = Field(gt=0)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class ClaimIn(BaseModel):
    driver: str
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class HandoverIn(BaseModel):
    otp: str


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle (haversine) distance in km."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _get(item_id: int) -> dict:
    if item_id not in SURPLUS:
        raise HTTPException(status_code=404, detail="Surplus listing not found")
    return SURPLUS[item_id]


@app.get("/")
def home():
    return {"service": "Food Rescue Network API", "version": VERSION, "radius_km": RADIUS_KM}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/surplus", status_code=201)
def create_surplus(body: SurplusIn):
    item_id = _counter["next"]
    _counter["next"] += 1
    SURPLUS[item_id] = {"id": item_id, **body.model_dump(), "status": "available", "_otp": None}
    return {"id": item_id, "status": "available"}


@app.get("/surplus/nearby")
def nearby(lat: float, lon: float):
    found = []
    for s in SURPLUS.values():
        if s["status"] != "available":
            continue
        d = distance_km(lat, lon, s["lat"], s["lon"])
        if d <= RADIUS_KM:
            found.append({**{k: v for k, v in s.items() if k != "_otp"}, "distance_km": round(d, 2)})
    return sorted(found, key=lambda x: x["distance_km"])


@app.post("/surplus/{item_id}/claim")
def claim(item_id: int, body: ClaimIn):
    s = _get(item_id)
    if s["status"] != "available":
        raise HTTPException(status_code=409, detail="Already claimed")
    d = distance_km(body.lat, body.lon, s["lat"], s["lon"])
    if d > RADIUS_KM:
        raise HTTPException(status_code=403, detail=f"Driver is {d:.1f} km away (limit {RADIUS_KM} km)")
    s["status"] = "claimed"
    s["driver"] = body.driver
    s["_otp"] = f"{secrets.randbelow(10**6):06d}"
    # In production the OTP is sent to the cafeteria; returned here for the demo.
    return {"id": item_id, "status": "claimed", "otp": s["_otp"]}


@app.post("/surplus/{item_id}/handover")
def handover(item_id: int, body: HandoverIn):
    s = _get(item_id)
    if s["status"] != "claimed":
        raise HTTPException(status_code=409, detail="Listing is not in claimed state")
    if not secrets.compare_digest(body.otp, s["_otp"]):
        raise HTTPException(status_code=400, detail="Invalid OTP")
    s["status"] = "delivered"
    s["_otp"] = None
    return {"id": item_id, "status": "delivered"}
