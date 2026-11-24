from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_text_analysis():
    r = client.post("/api/analyze", json={"text":"URGENT verify your bank KYC now", "channel":"sms"})
    assert r.status_code == 200
    assert 0 <= r.json()["risk_score"] <= 100

def test_url_analysis():
    r = client.post("/api/analyze-url", json={"url":"http://192.0.2.1/login"})
    assert r.status_code == 200
