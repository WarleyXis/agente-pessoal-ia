from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

import requests
from fastapi import APIRouter, HTTPException, Query, Request
from PIL import Image, UnidentifiedImageError
from starlette.concurrency import run_in_threadpool

from backend.memory.store import save_turn
from backend.tools.vision_tools import describe_image

router = APIRouter(prefix="/api")
MAX_MEDIA_BYTES = 5 * 1024 * 1024


async def read_media(request: Request, supported: set[str]) -> tuple[str, bytes]:
    media_type = request.headers.get("content-type", "").split(";")[0].strip()
    if media_type not in supported:
        raise HTTPException(415, "Formato de mídia indisponível.")
    data = bytearray()
    async for chunk in request.stream():
        if len(data) + len(chunk) > MAX_MEDIA_BYTES:
            raise HTTPException(413, "A mídia excede 5 MB.")
        data.extend(chunk)
    if not data:
        raise HTTPException(422, "O arquivo de mídia está vazio.")
    return media_type, bytes(data)


def transcribe(audio: bytes, suffix: str) -> str:
    from backend.voice.stt import transcribe_audio

    with TemporaryDirectory(prefix="atlas-voice-") as directory:
        path = Path(directory) / f"recording.{suffix}"
        path.write_bytes(audio)
        return transcribe_audio(str(path))


@router.post("/transcribe")
async def post_transcription(request: Request) -> dict:
    formats = {"audio/webm": "webm", "audio/ogg": "ogg", "audio/mp4": "mp4"}
    kind, audio = await read_media(request, set(formats))
    try:
        text = await run_in_threadpool(transcribe, audio, formats[kind])
    except (OSError, ValueError, ImportError, RuntimeError) as error:
        raise HTTPException(502, "Não foi possível transcrever. Confira a gravação e o modelo Whisper local.") from error
    if not text:
        raise HTTPException(422, "Nenhuma fala foi reconhecida.")
    return {"text": text}


def inspect_image(image: bytes, question: str) -> str:
    try:
        with Image.open(BytesIO(image), formats=["PNG"]) as frame:
            if frame.width * frame.height > 1920 * 1080:
                raise ValueError
            frame.verify()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as error:
        raise HTTPException(422, "A captura PNG não é válida.") from error
    try:
        output = describe_image(image, question)
    except requests.Timeout as error:
        raise HTTPException(504, "O modelo visual local demorou demais.") from error
    except (requests.RequestException, KeyError, ValueError) as error:
        raise HTTPException(502, "Confira se o Ollama e o modelo visual configurado estão disponíveis.") from error
    save_turn(question, output)
    return output


@router.post("/vision")
async def post_vision(request: Request, question: str = Query(min_length=1, max_length=1000)) -> dict:
    _, image = await read_media(request, {"image/png"})
    return {"response": await run_in_threadpool(inspect_image, image, question)}
