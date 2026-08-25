# Este arquivo cria a API HTTP do agente usando FastAPI. É através
# dela que o frontend (React) e outras interfaces conversam com o
# agente — em vez de só o terminal.

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.core.agent import Agent
from backend.core.config import settings

# Guardamos UMA instância do agente, criada uma única vez quando a
# API sobe — não uma nova a cada requisição.
agent: Agent | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent
    agent = Agent()
    yield
    agent = None


app = FastAPI(title=f"{settings.agent_name} API", lifespan=lifespan)

# CORS: autoriza o frontend (rodando em localhost:5173 durante o
# desenvolvimento) a fazer requisições para esta API. Em produção
# (Fase 20), essa lista seria restrita ao endereço real do app.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    """Formato esperado no corpo da requisição de POST /api/chat."""
    message: str


class ChatResponse(BaseModel):
    """Formato da resposta devolvida por POST /api/chat."""
    response: str


@app.get("/api/status")
def get_status() -> dict:
    """Endpoint simples para confirmar que a API está no ar."""
    return {"agent_name": settings.agent_name, "status": "online"}


@app.post("/api/chat", response_model=ChatResponse)
def post_chat(request: ChatRequest) -> ChatResponse:
    """Recebe uma mensagem do usuário e devolve a resposta do agente."""
    resposta = agent.respond(request.message)
    return ChatResponse(response=resposta)