
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import CORS_ORIGINS
from .schemas import AnalyzeRequest, UrlRequest
from .detector import analyze_text, analyze_url
from .database import init_db, save_analysis, recent_analyses
from starlette.middleware.base import BaseHTTPMiddleware


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )

        return response

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="CyberSahay API",
    version="1.1.0",
    description="Multilingual cyber-fraud awareness prototype",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.add_middleware(SecurityHeadersMiddleware)


@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception,
):
    logger.exception(
        "Unexpected server error on %s %s",
        request.method,
        request.url.path,
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": (
                "Something went wrong while processing your request. "
                "Please try again later."
            ),
        },
    )


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "CyberSahay API",
    }


@app.post("/api/analyze")
def analyze(request: AnalyzeRequest):
    result = analyze_text(
        request.text,
        input_mode=request.input_mode,
    )

    input_type = (
        "conversation"
        if request.input_mode == "conversation"
        else request.channel
    )

    save_analysis(
        input_type,
        result["category"],
        result["risk_score"],
    )

    return result


@app.post("/api/analyze-url")
def analyze_url_endpoint(request: UrlRequest):
    result = analyze_url(request.url)

    save_analysis(
        "url",
        result["category"],
        result["risk_score"],
    )

    return result


@app.get("/api/history")
def history():
    return {"items": recent_analyses()}
