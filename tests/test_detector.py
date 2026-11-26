
import pytest

from backend.app.detector import analyze_text, analyze_url


@pytest.mark.parametrize(
    "message",
    [
        "Hey, are we meeting for lunch today?",
        "Your appointment is confirmed for tomorrow.",
        "I have transferred the notes to your email.",
        "Please call me when you reach home.",
        "Your electricity bill payment was successful.",
    ],
)
def test_legitimate_messages_do_not_trigger_rule_signals(message):
    result = analyze_text(message)

    assert result["risk_score"] == 0
    assert result["category"] == "Lower risk"


@pytest.mark.parametrize(
    "message",
    [
        "Your OTP is 123456. Share it immediately.",
        "Congratulations! You won a prize. Pay a processing fee to claim it.",
        "Urgent! Verify your bank KYC details immediately.",
        "Your account will be blocked. Update your bank details now.",
    ],
)
def test_suspicious_messages_trigger_warning_signals(message):
    result = analyze_text(message)

    assert result["risk_score"] >= 30
    assert result["category"] in ("Needs caution", "High risk")
    assert len(result["explanation"]) > 0


def test_urgency_alone_does_not_automatically_mean_fraud():
    result = analyze_text(
        "Urgent, please call me when you reach the office."
    )

    assert result["risk_score"] == 16
    assert result["category"] == "Lower risk"


def test_legitimate_url_does_not_trigger_basic_url_warnings():
    result = analyze_url("https://example.com")

    assert result["risk_score"] == 0
    assert result["category"] == "Lower risk"


def test_http_url_triggers_caution():
    result = analyze_url("http://example.com")

    assert result["risk_score"] >= 18
    assert result["category"] == "Lower risk"


def test_url_with_user_info_requires_caution():
    result = analyze_url(
        "https://trusted.example.com@evil.example/login"
    )

    assert result["risk_score"] >= 30
    assert result["category"] in ("Needs caution", "High risk")


def test_sensitive_keyword_alone_is_not_proof_of_fraud():
    result = analyze_url("https://login.example.com")

    assert "sensitive-account keyword" in " ".join(
        result["explanation"]
    )
    assert result["risk_score"] == 18
    assert result["category"] == "Lower risk"
