from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Callable, Literal

import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, StrictBool, StringConstraints
from starlette.middleware.trustedhost import TrustedHostMiddleware

from backend.api.approvals import Approvals
from backend.api.reports import init_reports, router as reports_router
from backend.api.media import router as media_router
from backend.core.agent import Agent
from backend.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.agent = Agent()
    init_reports()
    app.state.approvals = Approvals()
    try:
        yield
    finally:
        app.state.approvals.close()


app = FastAPI(title=f"{settings.agent_name} API", lifespan=lifespan)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "[::1]", "testserver"])


@app.middleware("http")
async def local_origin(request: Request, call_next):
    origin = request.headers.get("origin")
    if origin and origin not in {settings.frontend_origin, str(request.base_url).rstrip("/")}:
        return JSONResponse({"detail": "Origem não autorizada."}, status_code=403)
    return await call_next(request)


class ChatRequest(BaseModel):
    message: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=12000)]


class PersonalAction(BaseModel):
    tool: Literal["open_url", "save_note"]
    arguments: dict


class Decision(BaseModel):
    approved: StrictBool


def run_model(operation: Callable):
    try:
        return operation()
    except requests.Timeout as error:
        raise HTTPException(504, "O modelo local demorou demais para responder.") from error
    except (requests.RequestException, ValueError, KeyError, TypeError, AttributeError) as error:
        raise HTTPException(502, "Confira se o Ollama está rodando e se o modelo configurado foi instalado.") from error
    except OverflowError as error:
        raise HTTPException(429, str(error)) from error


@app.get("/api/status")
def get_status() -> dict:
    return {"agent_name": settings.agent_name, "status": "online", "model": settings.ollama_model}


@app.post("/api/chat")
def post_chat(body: ChatRequest, request: Request) -> dict:
    execution = request.app.state.agent.run(body.message)
    return run_model(lambda: request.app.state.approvals.advance(execution, lambda: next(execution)))


@app.post("/api/actions")
def personal_action(body: PersonalAction, request: Request) -> dict:
    execution = request.app.state.agent.run_action(body.tool, body.arguments)
    return run_model(lambda: request.app.state.approvals.advance(execution, lambda: next(execution)))


@app.post("/api/approvals/{key}")
def decide(key: str, decision: Decision, request: Request) -> dict:
    execution = request.app.state.approvals.take(key)
    if execution is None:
        raise HTTPException(404, "A aprovação expirou ou já foi processada.")
    return run_model(lambda: request.app.state.approvals.advance(execution, lambda: execution.send(decision.approved)))


app.include_router(reports_router)
app.include_router(media_router)

dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if dist.is_dir():
    app.mount("/", StaticFiles(directory=dist, html=True), name="frontend")
