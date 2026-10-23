import pytest
from fastapi.testclient import TestClient

from app import main
from app.main import app, distance_km

client = TestClient(app)

PUNE = (18.5204, 73.8567)
NEAR = (18.5600, 73.8000)    # about 7 km from PUNE
FAR = (19.0760, 72.8777)     # Mumbai, far outside 10 km


@pytest.fixture(autouse=True)
def reset_state():
    main.SURPLUS.clear()
    main._counter["next"] = 1


def make_listing():
    r = client.post("/surplus", json={"cafeteria": "Main Canteen", "item": "Rice", "quantity_kg": 5,
                                      "lat": PUNE[0], "lon": PUNE[1]})
    assert r.status_code == 201
    return r.json()["id"]


def test_health_and_home():
    assert client.get("/health").json() == {"status": "ok"}
    body = client.get("/").json()
    assert "version" in body and body["radius_km"] == 10.0


def test_distance_zero_and_positive():
    assert distance_km(*PUNE, *PUNE) == pytest.approx(0, abs=1e-6)
    assert distance_km(*PUNE, *FAR) > 100


def test_invalid_quantity_rejected():
    r = client.post("/surplus", json={"cafeteria": "X", "item": "Y", "quantity_kg": 0, "lat": 1, "lon": 1})
    assert r.status_code == 422


def test_nearby_filters_by_radius():
    make_listing()
    assert len(client.get("/surplus/nearby", params={"lat": NEAR[0], "lon": NEAR[1]}).json()) == 1
    assert client.get("/surplus/nearby", params={"lat": FAR[0], "lon": FAR[1]}).json() == []


def test_claim_out_of_radius_forbidden():
    i = make_listing()
    r = client.post(f"/surplus/{i}/claim", json={"driver": "D1", "lat": FAR[0], "lon": FAR[1]})
    assert r.status_code == 403


def test_full_flow_with_otp():
    i = make_listing()
    r = client.post(f"/surplus/{i}/claim", json={"driver": "D1", "lat": NEAR[0], "lon": NEAR[1]})
    assert r.status_code == 200
    otp = r.json()["otp"]
    assert len(otp) == 6
    assert client.post(f"/surplus/{i}/claim", json={"driver": "D2", "lat": NEAR[0], "lon": NEAR[1]}).status_code == 409
    bad = "000000" if otp != "000000" else "111111"
    assert client.post(f"/surplus/{i}/handover", json={"otp": bad}).status_code == 400
    ok = client.post(f"/surplus/{i}/handover", json={"otp": otp})
    assert ok.status_code == 200 and ok.json()["status"] == "delivered"


def test_unknown_listing_404():
    assert client.post("/surplus/99/claim", json={"driver": "D", "lat": 1, "lon": 1}).status_code == 404
