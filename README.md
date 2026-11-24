# CyberSahay — Complete Starter Project

A single-folder starter for an AI-assisted cyber-fraud awareness platform.

## Included
- `frontend/`: React + TypeScript + Vite + Tailwind dashboard
- `backend/`: FastAPI API, text/URL analysis, SQLite history
- `ml/`: data inspection, preprocessing, SMS model training and evaluation
- `datasets/`: small clearly-labelled demo dataset, manifest and download locations
- `scripts/`: dataset downloader
- `tests/`: backend API tests
- `docs/`: architecture, data policy and development roadmap

## Requirements
- Python 3.11 or newer (Python 3.12 recommended)
- Node.js 20 or newer
- npm

## A. Start backend
Open a VS Code terminal in the project root, then:

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Backend health: http://127.0.0.1:8000/api/health  
API documentation: http://127.0.0.1:8000/docs

If `py -3.12` is unavailable, use `python -m venv .venv`.

## B. Start frontend
Open a SECOND VS Code terminal in the project root:

```powershell
cd frontend
npm install
npm run dev
```

Open the localhost URL printed by Vite (usually http://localhost:5173).

## C. Download datasets
Open another VS Code terminal in the project root:

```powershell
python -m pip install -r scripts/requirements.txt
python scripts/download_datasets.py
```

This downloads the SMS datasets supported by the script into `datasets/raw/`.
URL datasets are publisher links and must be downloaded manually; see `datasets/README.md`.

## D. Train the baseline SMS model (optional)
After datasets have downloaded, first inspect their format. The starter training script uses only
`datasets/demo_sms.csv` so the project runs immediately without external downloads:

```powershell
cd ml
python -m pip install -r requirements.txt
python train_sms_model.py
```

The trained model is saved to `ml/models/sms_model.joblib`. Restart the backend after training.

## Important
This is a learning/research prototype, not a production fraud verdict service. Risk scores are
heuristic indicators, not calibrated probabilities. A low score does not prove a message or URL
is safe. Never open submitted suspicious URLs. Never enter OTPs, passwords, PINs or banking data.

External datasets are NOT redistributed in this ZIP. Their downloader and source links are included.
Review each dataset's current license, terms, provenance and label quality before use. Keep synthetic
data separate from real-world evaluation data.
