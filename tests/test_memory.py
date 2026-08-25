# Testamos o armazenamento de memória usando um banco temporário,
# criado só para o teste, para não misturar com o histórico real
# do agente.

from backend.memory import store as memory_store


def test_save_and_load_history(tmp_path, monkeypatch):
    # Aponta o banco para um arquivo temporário, isolado deste teste.
    monkeypatch.setattr(memory_store, "DB_PATH", tmp_path / "test_memory.db")

    memory_store.init_db()
    memory_store.save_message("user", "oi")
    memory_store.save_message("assistant", "olá!")

    history = memory_store.load_recent_history()

    assert history == [
        {"role": "user", "content": "oi"},
        {"role": "assistant", "content": "olá!"},
    ]


def test_load_recent_history_respects_limit(tmp_path, monkeypatch):
    monkeypatch.setattr(memory_store, "DB_PATH", tmp_path / "test_memory.db")
    memory_store.init_db()

    for i in range(5):
        memory_store.save_message("user", f"mensagem {i}")

    history = memory_store.load_recent_history(limit=2)

    assert len(history) == 2
    assert history[-1]["content"] == "mensagem 4"  # a mais recente