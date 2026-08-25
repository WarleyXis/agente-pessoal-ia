# Armazena o histórico de conversas em um banco de dados SQLite —
# um banco simples, guardado num único arquivo, sem precisar
# instalar nem configurar nenhum servidor separado. Serve bem para
# um agente pessoal de um usuário só, rodando localmente.
#
# Quando o projeto precisar de busca por similaridade (RAG, Fase 15)
# ou múltiplos usuários simultâneos, vamos migrar para PostgreSQL —
# mas até lá, SQLite é suficiente e muito mais simples de configurar.

import sqlite3
from pathlib import Path

DB_PATH = Path("data") / "memory.db"

# Quantas mensagens recentes carregar como contexto. Isso existe
# porque modelos de IA têm um limite de quanto texto conseguem "ler"
# de uma vez (janela de contexto) — carregar a conversa inteira desde
# o começo ficaria caro e, em algum momento, simplesmente não caberia.
MAX_HISTORY_MESSAGES = 20


def _get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    """Cria a tabela de mensagens se ela ainda não existir."""
    with _get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )


def save_message(role: str, content: str) -> None:
    """Salva uma mensagem (do usuário ou do agente) no histórico."""
    with _get_connection() as conn:
        conn.execute(
            "INSERT INTO messages (role, content) VALUES (?, ?)",
            (role, content),
        )


def load_recent_history(limit: int = MAX_HISTORY_MESSAGES) -> list[dict]:
    """
    Carrega as últimas mensagens salvas, na ordem certa (mais antiga
    primeiro), prontas para virar contexto do agente.
    """
    with _get_connection() as conn:
        cursor = conn.execute(
            "SELECT role, content FROM messages ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        rows = cursor.fetchall()

    # As linhas vêm da mais nova pra mais antiga (por causa do DESC);
    # invertemos para a ordem cronológica certa antes de devolver.
    rows.reverse()
    return [{"role": role, "content": content} for role, content in rows]
