import re
import unicodedata


def detect_candidate_rules(text: str) -> list[str]:
    """
    Experimental contextual rules.
    These signals are candidates for evaluation, not final fraud verdicts.
    """

    t = unicodedata.normalize("NFC", str(text)).lower()
    signals = []

    # 1. QR code combined with UPI PIN to receive money/refund.
    qr_pattern = r"(qr\s*code|qr|ಕ್ಯೂಆರ್|ಕ್ಯೂ\s*ಆರ್)"
    pin_pattern = r"(upi\s*pin|ಯುಪಿಐ\s*ಪಿನ್|ಪಿನ್\s*ನಮೂದಿಸಿ|pin\s*enter)"

    receive_pattern = (
        r"(refund|cashback|receive|credit|account.?ge.?barut|"
        r"ಹಣ.*(ಬರುತ್ತೆ|ಬರುತ್ತದೆ|ಜಮೆ)|ರಿಫಂಡ್|ಕ್ಯಾಶ್.?ಬ್ಯಾಕ್)"
    )

    if (
        re.search(qr_pattern, t)
        and re.search(pin_pattern, t)
        and re.search(receive_pattern, t)
    ):
        signals.append("QR code and UPI PIN requested for receiving money")

    # 2. Remote access in a banking or payment-support context.
    remote_pattern = (
        r"\b(anydesk|quicksupport|teamviewer|remote access|screen share)\b|"
        r"ಸ್ಕ್ರೀನ್.?ಶೇರ್|ರಿಮೋಟ್.?ಆಕ್ಸೆಸ್"
    )

    financial_pattern = (
        r"\b(bank|banking|upi|refund|transaction|payment|account)\b|"
        r"ಬ್ಯಾಂಕ್|ಯುಪಿಐ|ರಿಫಂಡ್|ವಹಿವಾಟು|ಪಾವತಿ|ಖಾತೆ"
    )

    if re.search(remote_pattern, t) and re.search(financial_pattern, t):
        signals.append("Remote-access request in a financial-service context")

    # 3. Authority impersonation combined with arrest threats and pressure.
    authority_pattern = (
        r"\b(cbi|police|crime branch|customs|officer)\b|"
        r"ಸಿಬಿಐ|ಪೊಲೀಸ್|ಅಪರಾಧ ಶಾಖೆ|ಅಧಿಕಾರಿ"
    )

    threat_pattern = (
    r"\b(arrest|arrest warrant|warrant|custody)\b|"
    r"ಬಂಧನ|ಬಂಧನ ವಾರಂಟ್|ವಾರಂಟ್|ಅರೆಸ್ಟ್"
)

    pressure_pattern = (
        r"\b(do not disconnect|stay on the call|do not tell anyone)\b|"
        r"ಕರೆ ಕಡಿತಗೊಳಿಸಬೇಡಿ|ವಿಡಿಯೋ ಕಾಲ್‌ನಲ್ಲೇ ಇರಿ|"
        r"ಮನೆಯವರಿಗೆ.*ತಿಳಿಸಬೇಡಿ"
    )

    if (
        re.search(authority_pattern, t)
        and re.search(threat_pattern, t)
        and re.search(pressure_pattern, t)
    ):
        signals.append("Authority impersonation with arrest threats and isolation pressure")

    # 4. Recruitment combined with requests for financial identifiers.
    job_pattern = (
        r"\b(hiring|job|recruitment|work.from.home|intern|selected candidate)\b|"
        r"ಉದ್ಯೋಗ|ನೇಮಕಾತಿ|ಕೆಲಸ"
    )

    financial_data_pattern = (
        r"\b(bank.linked mobile|upi id|bank details|bank account)\b|"
        r"ಬ್ಯಾಂಕ್ ಖಾತೆ|ಯುಪಿಐ ಐಡಿ"
    )

    if re.search(job_pattern, t) and re.search(financial_data_pattern, t):
        signals.append("Job or recruitment message requests financial identifiers")


    # 5. UPI receive-request manipulation.
    upi_pattern = r"\bupi\b|ಯುಪಿಐ"

    collect_request_pattern = (
        r"\breceive request\b|"
        r"\brequest kalisu\b|"
        r"ಕಲೆಕ್ಟ್.?ರಿಕ್ವೆಸ್ಟ್|"
        r"ರಿಸೀವ್.?ರೆಕ್ವೆಸ್ಟ್"
    )

    advance_context_pattern = (
        r"\badvance\b|\bpayment\b|\bseller\b|"
        r"ಅಡ್ವಾನ್ಸ್|ಮುಂಗಡ"
    )

    if (
        re.search(upi_pattern, t)
        and re.search(collect_request_pattern, t)
        and re.search(advance_context_pattern, t)
    ):
        signals.append(
            "UPI receive request combined with an advance-payment context"
        )
    return signals
