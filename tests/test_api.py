# Testamos a API sem precisar realmente subir um servidor na porta
# 8000 — o TestClient do FastAPI simula as requisições diretamente.

from fastapi.testclient import TestClient

from backend.api.app import app


def test_status_endpoint():
    with TestClient(app) as client:
        response = client.get("/api/status")
        assert response.status_code == 200
        assert response.json()["status"] == "online"