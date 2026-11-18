import json
import subprocess
import sys
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, StrictBool

from backend.core.config import settings
from backend.memory import store

router = APIRouter(prefix="/api")


class ReviewRequest(BaseModel):
    project: str
    include_tests: StrictBool = False


class ReviewDecision(BaseModel):
    approved: StrictBool


def projects() -> dict:
    try:
        data = json.loads(Path(settings.projects_file).read_text(encoding="utf-8"))
        if not isinstance(data, dict) or any(not isinstance(item, dict) for item in data.values()):
            raise ValueError
        return data
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as error:
        raise HTTPException(503, "Confira o arquivo de projetos do Atlas.") from error


def init_reports() -> None:
    with closing(store._get_connection()) as conn, conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                document TEXT NOT NULL
            )
        """)
        # A synchronous worker cannot continue after the server stops.
        rows = conn.execute("SELECT id, document FROM reports").fetchall()
        for key, document in rows:
            report = json.loads(document)
            if report["tests"]["state"] == "running":
                report["tests"] = {"state": "interrupted"}
                conn.execute("UPDATE reports SET document = ? WHERE id = ?", (json.dumps(report), key))


def run_command(command: list[str], cwd: Path, timeout: int) -> dict:
    try:
        result = subprocess.run(
            command, cwd=cwd, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"state": "timeout"}
    except OSError as error:
        return {"state": "unavailable", "output": error.strerror}
    return {
        "state": "passed" if result.returncode == 0 else "failed",
        "exit_code": result.returncode,
        "output": (result.stdout + result.stderr).strip()[:12000],
    }


@router.get("/projects")
def list_projects() -> list[str]:
    return sorted(projects())


@router.post("/reports")
def create_report(request: ReviewRequest) -> dict:
    project = projects().get(request.project)
    if project is None:
        raise HTTPException(404, "Projeto não cadastrado.")
    folder = project.get("path")
    if not isinstance(folder, str):
        raise HTTPException(422, "Configure o caminho absoluto do projeto.")
    cwd = Path(folder).expanduser()
    if not cwd.is_absolute() or not cwd.is_dir():
        raise HTTPException(422, "A pasta cadastrada não está acessível neste computador.")
    cwd = cwd.resolve()
    interpreter = project.get("python", sys.executable)
    if not isinstance(interpreter, str) or not Path(interpreter).is_absolute():
        raise HTTPException(422, "Configure o caminho absoluto do Python do projeto.")
    if cwd.joinpath(".git").exists():
        git = {
            "status": run_command(["git", "status", "--short", "--branch"], cwd, 10),
            "commits": run_command(["git", "log", "-5", "--oneline"], cwd, 10),
        }
    else:
        git = {"state": "no_git"}
    report = {
        "id": uuid4().hex, "project": request.project, "path": str(cwd),
        "created_at": datetime.now(timezone.utc).isoformat(), "git": git,
        "tests": {"state": "pending", "command": [interpreter, "-m", "pytest", "-q"]} if request.include_tests
        else {"state": "not_requested"},
    }
    with closing(store._get_connection()) as conn, conn:
        conn.execute("INSERT INTO reports VALUES (?, ?)", (report["id"], json.dumps(report)))
    return report


@router.get("/reports")
def list_reports() -> list[dict]:
    with closing(store._get_connection()) as conn:
        rows = conn.execute("SELECT document FROM reports ORDER BY rowid DESC LIMIT 20").fetchall()
    return [json.loads(row[0]) for row in rows]


@router.post("/reports/{key}/decision")
def decide_report(key: str, decision: ReviewDecision) -> dict:
    with closing(store._get_connection()) as conn, conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT document FROM reports WHERE id = ?", (key,)).fetchone()
        if row is None:
            raise HTTPException(404, "Relatório não encontrado.")
        report = json.loads(row[0])
        tests = report["tests"]
        if tests["state"] != "pending":
            raise HTTPException(409, "Esta decisão já foi processada.")
        tests["state"] = "running" if decision.approved else "declined"
        conn.execute("UPDATE reports SET document = ? WHERE id = ?", (json.dumps(report), key))

    if decision.approved:
        report["tests"] = {"command": tests["command"], **run_command(tests["command"], Path(report["path"]), 120)}
        with closing(store._get_connection()) as conn, conn:
            conn.execute("UPDATE reports SET document = ? WHERE id = ?", (json.dumps(report), key))
    return report
