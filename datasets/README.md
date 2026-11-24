# CyberSahay datasets

The ZIP includes `demo_sms.csv` only as a tiny runnable example. It is not enough for reliable
research or production performance claims.

## SMS sources
- UCI SMS Spam Collection: https://archive.ics.uci.edu/dataset/228/sms+spam+collection
- Scam/Ham India: https://huggingface.co/datasets/carnageiron/scam-ham-india
- Indian Scam SMS Synthetic Audited: https://huggingface.co/datasets/Ridham115/indian-scam-sms-synthetic-audited
- BSIS Indian Scam dataset: https://huggingface.co/datasets/harshcasper/bsis

## URL / phishing sources
- LegitPhish v2: https://data.mendeley.com/datasets/hx4m73v2sf/2
- URL-Phish: https://data.mendeley.com/datasets/65z9twcx3r/1

Use `python scripts/download_datasets.py` for the automated SMS downloads. URL dataset downloads
are manual from the publisher pages. Check current access and licensing terms.

## Data handling
- Preserve original source labels and add normalized labels in a separate column.
- Keep synthetic and real-world sources separate.
- Audit missing values, duplicates, source overlap and label quality.
- Do not use synthetic-only test results as real-world accuracy.
- Never fetch or open URLs in phishing datasets during preprocessing.
