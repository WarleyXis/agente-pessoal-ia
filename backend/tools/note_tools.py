import os
import re
from pathlib import Path, PureWindowsPath
from tempfile import NamedTemporaryFile
from threading import Lock

from backend.core.config import settings
from backend.tools.base import RiskLevel, Tool

NOTE_NAME = r"^[A-Za-z0-9][A-Za-z0-9 _-]{0,75}\.(txt|md)$"
MAX_NOTE_BYTES = 128 * 1024
note_lock = Lock()


class SaveNoteTool(Tool):
    name = "save_note"
    domain = "notes"
    risk_level = RiskLevel.MEDIUM
    description = (
        "Cria uma nota .txt ou .md ou acrescenta texto ao final de uma nota existente. "
        "Usa a pasta de notas do Atlas e pede aprovação antes de gravar."
    )

    def __init__(self) -> None:
        self.root = Path(settings.notes_directory).expanduser().resolve()

    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "pattern": NOTE_NAME},
                "content": {"type": "string", "minLength": 1, "maxLength": 10000},
                "mode": {"enum": ["create", "append"]},
            },
            "required": ["filename", "content", "mode"],
        }

    def note_path(self, filename: str) -> Path:
        if not re.fullmatch(NOTE_NAME, filename) or PureWindowsPath(filename).is_reserved():
            raise ValueError("Use um nome simples terminado em .txt ou .md.")
        return self.root / filename

    def approval_details(self, arguments: dict) -> dict:
        return {**arguments, "path": str(self.note_path(arguments["filename"]))}

    def execute(self, filename: str, content: str, mode: str) -> str:
        path = self.note_path(filename)
        content = content.encode("utf-8")
        with note_lock:
            if self.root.resolve() != self.root or path.is_symlink():
                return "A pasta ou a nota mudou de destino. Nenhuma alteração foi feita."
            if mode == "create":
                self.root.mkdir(parents=True, exist_ok=True)
                try:
                    with path.open("xb") as file:
                        file.write(content)
                except FileExistsError:
                    return f"A nota já existe em {path}. Use a opção de acrescentar texto."
                return f"Nota criada em {path}."
            if mode != "append" or not path.is_file():
                return "Para acrescentar texto, escolha uma nota existente."
            with path.open("rb") as file:
                snapshot = os.fstat(file.fileno())
                previous = file.read(MAX_NOTE_BYTES + 1)
            separator = b"\n" if previous and not previous.endswith(b"\n") else b""
            if len(previous) + len(separator) + len(content) > MAX_NOTE_BYTES:
                return "A nota excederia o limite de 128 KB."
            pending = None
            try:
                with NamedTemporaryFile(dir=self.root, delete=False) as temporary:
                    pending = Path(temporary.name)
                    temporary.write(previous + separator + content)
                current = path.stat()
                changed = (snapshot.st_mtime_ns, snapshot.st_size) != (current.st_mtime_ns, current.st_size)
                if path.is_symlink() or not os.path.samestat(snapshot, current) or changed:
                    return "A nota mudou durante a gravação. Confira o arquivo e tente novamente."
                os.replace(pending, path)
            finally:
                if pending is not None:
                    pending.unlink(missing_ok=True)
        return f"Texto acrescentado em {path}."
