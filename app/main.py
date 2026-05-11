from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response

try:
    from app.agent import build_response
    from app.dashboard import DASHBOARD_HTML
    from app.models import ChatRequest, ChatResponse
except ModuleNotFoundError:  # pragma: no cover - supports file-based runners
    from agent import build_response
    from dashboard import DASHBOARD_HTML
    from models import ChatRequest, ChatResponse


app = FastAPI(title="SHL Conversational Assessment Recommender")


@app.get("/", response_class=HTMLResponse)
def root() -> HTMLResponse:
    return HTMLResponse(DASHBOARD_HTML)


@app.get("/favicon.ico")
def favicon() -> Response:
    return Response(status_code=204)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    return build_response(request.messages)
