
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



@pytest.mark.parametrize(
    "message",
    [
        # Kannada: account-blocking threat and OTP disclosure
        "ನಿಮ್ಮ ಬ್ಯಾಂಕ್ ಖಾತೆಯನ್ನು ಇಂದು ಬ್ಲಾಕ್ ಮಾಡಲಾಗುತ್ತದೆ. "
        "ತಕ್ಷಣ ನಿಮ್ಮ KYC ಪರಿಶೀಲಿಸಲು ಈ ಲಿಂಕ್ ಕ್ಲಿಕ್ ಮಾಡಿ. "
        "ನಿಮ್ಮ OTP ಅನ್ನು ಹಂಚಿಕೊಳ್ಳಿ.",

        # Hindi: account closure threat and OTP disclosure
        "आपका बैंक खाता आज बंद कर दिया जाएगा। "
        "तुरंत अपना KYC सत्यापित करें और अपना OTP साझा करें।",
    ],
)
def test_kannada_and_hindi_scam_messages_trigger_warnings(message):
    result = analyze_text(message)

    assert result["risk_score"] >= 30
    assert result["category"] in ("Needs caution", "High risk")
    assert len(result["explanation"]) > 0


@pytest.mark.parametrize(
    "message",
    [
        "ನಾಳೆ ಬೆಳಿಗ್ಗೆ ಭೇಟಿಯಾಗೋಣ. ನಿಮ್ಮನ್ನು ನೋಡಲು ಸಂತೋಷವಾಗುತ್ತದೆ.",
        "कल सुबह मिलते हैं। आपसे मिलकर खुशी होगी।",
    ],
)
def test_legitimate_kannada_and_hindi_messages_are_not_high_risk(message):
    result = analyze_text(message)

    assert result["risk_score"] < 65
    assert result["category"] != "High risk"
