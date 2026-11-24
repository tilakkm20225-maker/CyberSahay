import re
from pathlib import Path
import joblib

MODEL_PATH = Path(__file__).resolve().parents[2] / "ml" / "models" / "sms_model.joblib"
_model = None

def load_model():
    global _model
    if _model is None and MODEL_PATH.exists():
        try:
            _model = joblib.load(MODEL_PATH)
        except Exception:
            _model = None
    return _model

def analyze_text(text: str):
    signals = []
    t = text.lower()
    rules = [
        (r"\b(otp|one[- ]time password)\b", "Mentions an OTP or one-time password"),
        (r"\b(urgent|immediately|today|within 24 hours)\b", "Uses urgency or pressure"),
        (r"\b(verify|update)\b.{0,60}\b(kyc|account|bank|details)\b", "Requests account or KYC verification"),
        (r"\b(prize|winner|reward|cashback|free gift)\b", "Promises a prize or reward"),
        (r"\b(processing fee|joining fee|pay.{0,15}fee)\b", "Requests an upfront fee"),
        (r"https?://|www\.", "Contains a web link"),
    ]
    for pattern, reason in rules:
        if re.search(pattern, t):
            signals.append(reason)

    confidence = 0.0
    predicted = None
    model = load_model()
    if model is not None:
        try:
            probs = model.predict_proba([text])[0]
            classes = list(model.classes_)
            idx = int(probs.argmax())
            predicted = str(classes[idx])
            confidence = float(probs[idx])
        except Exception:
            pass

    # This is an explainable heuristic score, NOT a calibrated fraud probability.
    score = min(95, len(signals) * 16)
    if predicted == "spam":
        score = max(score, int(45 + confidence * 35))
    elif predicted == "ham":
        score = min(score, 35)

    category = "High risk" if score >= 65 else "Needs caution" if score >= 30 else "Lower risk"
    if not signals:
        signals = ["No configured warning pattern was detected"]
    recommendation = (
        "Do not click links or share OTPs, passwords or payment details. Verify independently using the official app or phone number."
        if score >= 30 else
        "No strong configured warning pattern was found. This does not prove the message is safe; verify unexpected requests independently."
    )
    return {"category": category, "risk_score": score, "confidence": round(confidence, 3),
            "explanation": signals, "recommendation": recommendation}

def analyze_url(url: str):
    from urllib.parse import urlparse
    candidate = url if "://" in url else "https://" + url
    parsed = urlparse(candidate)
    host = (parsed.hostname or "").lower()
    signals = []
    if parsed.scheme != "https":
        signals.append("URL does not use HTTPS")
    if not host or "." not in host:
        signals.append("Hostname format looks unusual")
    if re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", host):
        signals.append("Uses a raw IP address instead of a domain")
    if len(host) > 45:
        signals.append("Unusually long hostname")
    if host.count("-") >= 3:
        signals.append("Hostname contains several hyphens")
    if "@" in url:
        signals.append("Contains an @ symbol that may obscure the destination")
    if any(word in host for word in ("login", "verify", "secure", "wallet", "banking")):
        signals.append("Contains a sensitive-account keyword; this alone does not prove fraud")
    score = min(95, len(signals) * 18)
    return {"category": "High risk" if score >= 65 else "Needs caution" if score >= 30 else "Lower risk",
            "risk_score": score, "confidence": 0.0,
            "explanation": signals or ["No basic URL warning signal was detected"],
            "recommendation": "Do not open suspicious links. Check the domain independently and use the official website or app."}
