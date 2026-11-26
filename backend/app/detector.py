
import re
from pathlib import Path

import joblib


ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = ROOT / "ml" / "models"

LEGACY_MODEL_PATH = MODEL_DIR / "sms_model.joblib"
SINGLE_MODEL_PATH = MODEL_DIR / "bsis_single_message_fpr_controlled.joblib"
CONVERSATION_MODEL_PATH = MODEL_DIR / "bsis_multilingual_fpr_controlled.joblib"

SINGLE_THRESHOLD = 0.7236015808024677
CONVERSATION_THRESHOLD = 0.74818514

_models = {}


def load_model(name, path):
    if name not in _models:
        _models[name] = None

        if path.exists():
            try:
                _models[name] = joblib.load(path)
            except Exception as exc:
                print(f"Could not load {name} model: {exc}")

    return _models[name]


def contains_unsupported_script(text: str) -> bool:
    """Detect Devanagari or Kannada script."""
    for char in text:
        code = ord(char)

        if 0x0900 <= code <= 0x097F:
            return True

        if 0x0C80 <= code <= 0x0CFF:
            return True

    return False


def get_rule_signals(text: str):
    signals = []
    t = text.lower()

    rules = [
    (
    r"\b(otp|one[- ]time password)\b.{0,100}"
    r"(?<!do not )(?<!don't )(?<!never )"
    r"\b(share|send|tell|reveal|provide|forward|disclose)\b"
    r"|\b(?<!do not )(?<!don't )(?<!never )"
    r"(share|send|tell|reveal|provide|forward|disclose)\b"
    r".{0,100}\b(otp|one[- ]time password)\b",
    "Requests disclosure of an OTP or one-time password",
    ),
    (
        r"\b(otp|one[- ]time password)\b",
        "Mentions an OTP or one-time password",
    ),
    (
        r"\b(urgent|immediately|act now|within 24 hours|final warning)\b",
        "Uses urgency or pressure",
    ),
    (
        r"\b(verify|update)\b.{0,60}\b(kyc|account|bank|details)\b",
        "Requests account or KYC verification",
    ),
    (
        r"(?=.*\b(?:account|bank account)\b.{0,50}\b(?:block|blocked|suspend|suspended|close|closed|restrict|restricted)\b)(?=.*\b(?:verify|update|confirm)\b.{0,60}\b(?:kyc|account|bank|details)\b)",
        "Combines an account restriction threat with a request to update sensitive details",
    ),
    (
        r"\b(you(?:'ve| have)?\s+won|winner|prize|free gift|claim(?:\s+your)?\s+reward|(?:claim|redeem|collect)\s+(?:your\s+)?cashback)\b",
        "Promises a prize or reward",
    ),
    (
        r"\b(processing fee|joining fee|pay.{0,15}fee)\b",
        "Requests an upfront fee",
    ),
    (
        r"https?://|www\.",
        "Contains a web link",
    ),
]

    for pattern, reason in rules:
        if re.search(pattern, t):
            signals.append(reason)

    return signals


def classify_with_bsis(text: str, input_mode: str):
    if input_mode == "conversation":
        model_name = "conversation"
        model_path = CONVERSATION_MODEL_PATH
        threshold = CONVERSATION_THRESHOLD
    else:
        model_name = "single_message"
        model_path = SINGLE_MODEL_PATH
        threshold = SINGLE_THRESHOLD

    model = load_model(model_name, model_path)

    if model is None:
        return {
            "available": False,
            "prediction": None,
            "score": None,
            "threshold": threshold,
            "model_name": model_name,
        }

    try:
        score = float(model.predict_proba([text])[0][1])

        return {
            "available": True,
            "prediction": "scam" if score >= threshold else "not_flagged",
            "score": round(score, 4),
            "threshold": threshold,
            "model_name": model_name,
        }

    except Exception as exc:
        print(f"BSIS inference failed: {exc}")

        return {
            "available": False,
            "prediction": None,
            "score": None,
            "threshold": threshold,
            "model_name": model_name,
        }


def analyze_text(text: str, input_mode: str = "single_message"):
    signals = get_rule_signals(text)

    rule_score = min(95, len(signals) * 16)

    bsis = classify_with_bsis(text, input_mode)

    # Keep the old English SMS model as an independent legacy signal.
    legacy_model_used = False
    legacy_spam_probability = 0.0

    if input_mode == "single_message" and not contains_unsupported_script(text):
        legacy_model = load_model("legacy", LEGACY_MODEL_PATH)

        if legacy_model is not None:
            try:
                probabilities = legacy_model.predict_proba([text])[0]
                classes = list(legacy_model.classes_)

                if "spam" in classes:
                    legacy_spam_probability = float(
                        probabilities[classes.index("spam")]
                    )
                    legacy_model_used = True

            except Exception as exc:
                print(f"Legacy SMS inference failed: {exc}")

    # The BSIS score is a classifier output, not a calibrated probability.
    bsis_score = 0

    if bsis["available"] and bsis["prediction"] == "scam":
        bsis_score = 80

        signals.append(
            f"BSIS {bsis['model_name']} classifier flagged this input"
        )

    legacy_score = 0

    if legacy_model_used and legacy_spam_probability >= 0.70:
        legacy_score = 60
        signals.append("Legacy English SMS model detected spam-like content")

    score = max(rule_score, bsis_score, legacy_score)

    if score >= 65:
        category = "High risk"
    elif score >= 30:
        category = "Needs caution"
    else:
        category = "Lower risk"

    if not signals:
        signals = ["No configured warning pattern was detected"]

    recommendation = (
        "Do not click links or share OTPs, passwords or payment details. "
        "Verify independently using the official app or phone number."
        if score >= 30
        else
        "No strong configured warning pattern was found. "
        "This does not prove the input is safe. Verify unexpected requests independently."
    )

    if bsis["available"]:
        model_status = f"BSIS {bsis['model_name']} model used"
    else:
        model_status = f"BSIS {bsis['model_name']} model unavailable"

    return {
        "category": category,
        "risk_score": score,
        "confidence": bsis["score"] if bsis["available"] else 0.0,
        "model_prediction": bsis["prediction"],
        "model_used": bsis["available"],
        "model_status": model_status,
        "input_mode": input_mode,
        "classifier_score": bsis["score"],
        "classifier_threshold": bsis["threshold"],
        "classifier_model": bsis["model_name"],
        "legacy_model_used": legacy_model_used,
        "legacy_spam_score": round(legacy_spam_probability, 4),
        "explanation": signals,
        "recommendation": recommendation,
        "score_note": (
            "Classifier score is not a calibrated fraud probability. "
            "Risk score is a heuristic indicator."
        ),
    }


def analyze_url(url: str):
    from urllib.parse import urlparse

    candidate = url if "://" in url else "https://" + url

    try:
        parsed = urlparse(candidate)
        host = (parsed.hostname or "").lower()
    except ValueError:
        return {
            "category": "Needs caution",
            "risk_score": 30,
            "confidence": 0.0,
            "explanation": ["URL format is invalid or malformed"],
            "recommendation": (
                "Do not open this link. Verify the URL "
                "through the official website or app."
            ),
        }

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
        signals.append(
            "Contains an @ symbol that may obscure the destination"
        )

    if any(
        word in host
        for word in ("login", "verify", "secure", "wallet", "banking")
    ):
        signals.append(
            "Contains a sensitive-account keyword; "
            "this alone does not prove fraud"
        )

    score = min(95, len(signals) * 18)

    # URLs containing user-info syntax deserve at least caution.
    if "@" in url:
        score = max(score, 30)

    return {
        "category": (
            "High risk"
            if score >= 65
            else "Needs caution"
            if score >= 30
            else "Lower risk"
        ),
        "risk_score": score,
        "confidence": 0.0,
        "explanation": (
            signals or ["No basic URL warning signal was detected"]
        ),
        "recommendation": (
            "Do not open suspicious links. Check the domain independently "
            "and use the official website or app."
        ),
    }
