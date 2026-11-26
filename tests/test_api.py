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

from backend.app.detector import analyze_text, contains_unsupported_script


def test_today_alone_is_not_urgency():
    result = analyze_text("Hey, are we meeting for lunch today?")
    assert "Uses urgency or pressure" not in result["explanation"]



def test_kannada_script_skips_english_model():
    message = chr(0x0CA8)
    result = analyze_text(message)

    assert contains_unsupported_script(message)
    assert result["legacy_model_used"] is False
    assert result["legacy_spam_score"] == 0.0


def test_hindi_script_skips_english_model():
    message = chr(0x0906)
    result = analyze_text(message)

    assert contains_unsupported_script(message)
    assert result["legacy_model_used"] is False
    assert result["legacy_spam_score"] == 0.0


def test_text_too_short_returns_422():
    response = client.post(
        "/api/analyze",
        json={"text": "Hi"}
    )
    assert response.status_code == 422


def test_text_too_long_returns_422():
    response = client.post(
        "/api/analyze",
        json={"text": "A" * 10001}
    )
    assert response.status_code == 422


def test_invalid_channel_returns_422():
    response = client.post(
        "/api/analyze",
        json={
            "text": "This is a normal test message",
            "channel": "telegram"
        }
    )
    assert response.status_code == 422


def test_invalid_input_mode_returns_422():
    response = client.post(
        "/api/analyze",
        json={
            "text": "This is a normal test message",
            "input_mode": "unknown"
        }
    )
    assert response.status_code == 422


def test_url_too_short_returns_422():
    response = client.post(
        "/api/analyze-url",
        json={"url": "abc"}
    )
    assert response.status_code == 422


def test_missing_text_returns_422():
    response = client.post(
        "/api/analyze",
        json={}
    )
    assert response.status_code == 422


def test_whitespace_only_text_returns_422():
    response = client.post(
        "/api/analyze",
        json={"text": "   "}
    )
    assert response.status_code == 422

def test_malformed_url_returns_controlled_response():
    response = client.post(
        "/api/analyze-url",
        json={"url": "http://[invalid"}
    )

    assert response.status_code == 200

    result = response.json()
    assert result["category"] == "Needs caution"
    assert result["risk_score"] == 30
    assert "invalid or malformed" in result["explanation"][0]

def test_url_with_at_symbol_requires_caution():
    response = client.post(
        "/api/analyze-url",
        json={
            "url": "https://trusted.example.com@evil.example/login"
        }
    )

    assert response.status_code == 200

    result = response.json()
    assert result["category"] == "Needs caution"
    assert result["risk_score"] >= 30



def test_unexpected_error_returns_generic_500_response(monkeypatch):
    from fastapi.testclient import TestClient
    from backend.app import main

    def raise_unexpected_error(*args, **kwargs):
        raise RuntimeError("Internal test failure")

    monkeypatch.setattr(
        main,
        "analyze_text",
        raise_unexpected_error,
    )

    # Disable exception re-raising so we can inspect the HTTP 500 response.
    with TestClient(
        main.app,
        raise_server_exceptions=False,
    ) as error_client:

        response = error_client.post(
            "/api/analyze",
            json={
                "text": "This is a test message",
                "channel": "sms",
                "input_mode": "single_message",
            },
        )

    assert response.status_code == 500
    assert response.json()["error"] == "Internal server error"
    assert "Internal test failure" not in response.text
