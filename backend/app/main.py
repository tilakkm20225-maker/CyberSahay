from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import CORS_ORIGINS
from .schemas import AnalyzeRequest, UrlRequest
from .detector import analyze_text, analyze_url
from .database import init_db, save_analysis, recent_analyses

app = FastAPI(title="CyberSahay API", version="1.0.0",
              description="Educational cyber-fraud awareness prototype")
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS,
                   allow_credentials=False, allow_methods=["GET", "POST"],
                   allow_headers=["*"])

@app.on_event("startup")
def startup():
    init_db()

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "CyberSahay API"}

@app.post("/api/analyze")
def analyze(request: AnalyzeRequest):
    result = analyze_text(request.text)
    save_analysis(request.channel, result["category"], result["risk_score"])
    return result

@app.post("/api/analyze-url")
def analyze_url_endpoint(request: UrlRequest):
    result = analyze_url(request.url)
    save_analysis("url", result["category"], result["risk_score"])
    return result

@app.get("/api/history")
def history():
    return {"items": recent_analyses()}
