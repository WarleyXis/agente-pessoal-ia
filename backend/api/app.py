# Este arquivo cria a API HTTP do agente usando FastAPI. É através
# dela que, futuramente, o frontend (React) e outras interfaces vão
# conversar com o agente — em vez de só o terminal.

from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

from backend.core.agent import Agent
from backend.core.config import settings

# Guardamos UMA instância do agente, criada uma única vez quando a
# API sobe — não uma nova a cada requisição. Isso importa porque o
# Agent carrega o histórico de memória na criação; criar um novo a
# cada mensagem faria ele "esquecer" o que aconteceu na própria
# requisição anterior da mesma conversa.
agent: Agent | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Roda uma vez quando a API inicia (antes do 'yield') e uma vez
    quando ela desliga (depois do 'yield'). É aqui que criamos o
    Agent, em vez de criar um novo a cada chamada.
    """
    global agent
    agent = Agent()
    yield
    agent = None


app = FastAPI(title=f"{settings.agent_name} API", lifespan=lifespan)


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