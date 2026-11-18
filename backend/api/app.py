import logging
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
from backend.core.llm_provider import OllamaResponseError
from backend.core.ollama_timing import current_timing, OllamaTiming

logger = logging.getLogger(__name__)


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
    spoken: StrictBool = False
    fast: StrictBool = False


class PersonalAction(BaseModel):
    tool: Literal["open_url", "save_note"]
    arguments: dict


class Decision(BaseModel):
    approved: StrictBool


def run_model(operation: Callable):
    timing = OllamaTiming()
    token = current_timing.set(timing)
    try:
        output = operation()
        if timing.calls:
            output["ollama_timing"] = timing.public_data()
        return output
    except requests.ConnectTimeout as error:
        raise HTTPException(504, f"Tempo esgotado ao conectar ao Ollama em {settings.ollama_base_url}.") from error
    except requests.Timeout as error:
        raise HTTPException(504, f"O Ollama demorou demais para responder com {timing.model or settings.ollama_model}.") from error
    except requests.ConnectionError as error:
        raise HTTPException(502, f"Não consegui conectar ao Ollama em {settings.ollama_base_url}.") from error
    except requests.HTTPError as error:
        response = error.response
        status = response.status_code if response is not None else None
        try:
            payload = response.json() if response is not None else {}
        except ValueError:
            payload = {}
        detail = payload.get("error") if isinstance(payload, dict) else None
        detail = " ".join(detail.split())[:400] if isinstance(detail, str) else ""
        model = timing.model or settings.ollama_model
        if status == 404 and "model" in detail.lower() and "not found" in detail.lower():
            raise HTTPException(502, f"O Ollama não encontrou {model}. Rode: ollama pull {model}") from error
        label = f"O Ollama recusou a consulta com {model}"
        if status is not None:
            label += f" (HTTP {status})"
        raise HTTPException(502, f"{label}. {detail}".rstrip()) from error
    except OllamaResponseError as error:
        raise HTTPException(502, str(error)) from error
    except requests.RequestException as error:
        logger.exception("Falha na solicitação ao Ollama")
        raise HTTPException(502, "Erro ao enviar a solicitação ao Ollama. Confira o endereço configurado.") from error
    except OverflowError as error:
        raise HTTPException(429, str(error)) from error
    except Exception as error:
        logger.exception("Erro interno ao processar o pedido do Atlas")
        raise HTTPException(500, f"Erro interno no Atlas ({type(error).__name__}).") from error
    finally:
        current_timing.reset(token)


@app.get("/api/status")
def get_status() -> dict:
    return {
        "agent_name": settings.agent_name, "status": "online",
        "model": settings.ollama_model, "fast_model": settings.ollama_fast_model,
    }


@app.post("/api/chat")
def post_chat(body: ChatRequest, request: Request) -> dict:
    execution = request.app.state.agent.run(body.message, spoken=body.spoken, fast=body.fast)
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
