# Ferramenta que permite ao agente "ver" a tela do usuário: tira um
# screenshot e usa um modelo de visão (rodando local via Ollama)
# para descrever ou responder perguntas sobre o que está nela.

import base64
from io import BytesIO

import requests
from PIL import ImageGrab

from backend.core.config import settings
from backend.tools.base import RiskLevel, Tool


class DescribeScreenTool(Tool):
    name = "describe_screen"
    description = (
        "Tira um screenshot da tela atual e descreve o que está nela, "
        "ou responde uma pergunta específica sobre o conteúdo visível. "
        "Use quando o usuário perguntar sobre o que está na tela, um "
        "erro visível, ou pedir para 'ver' algo."
    )
    # Captura a tela inteira, que pode conter informação sensível
    # (senhas visíveis, conversas privadas, etc) — por isso pede
    # aprovação antes de rodar, mesmo não sendo uma ação destrutiva.
    risk_level = RiskLevel.MEDIUM
    domain = "vision"

    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": (
                        "O que perguntar sobre a tela. Use algo genérico "
                        "como 'descreva o que está na tela' se não houver "
                        "uma pergunta específica."
                    ),
                }
            },
            "required": ["question"],
        }

    def execute(self, question: str = "Descreva o que está na tela.", **kwargs) -> str:
        screenshot = ImageGrab.grab()

        # Converte a imagem para base64 — o formato que a API do
        # Ollama espera para receber imagens.
        buffer = BytesIO()
        screenshot.save(buffer, format="PNG")
        image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        # Nota: aqui conversamos direto com o Ollama, sem passar pelo
        # LLMProvider — porque visão usa um modelo diferente do texto
        # normal. É uma simplificação consciente por agora; unificar
        # isso na abstração de provider é um refinamento futuro.
        response = requests.post(
            f"{settings.ollama_base_url}/api/chat",
            json={
                "model": settings.ollama_vision_model,
                "messages": [
                    {"role": "user", "content": question, "images": [image_base64]}
                ],
                "stream": False,
            },
            timeout=180,  # modelos de visão são mais lentos que os de texto
        )
        response.raise_for_status()
        return response.json()["message"]["content"]