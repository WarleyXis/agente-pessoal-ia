// Este arquivo centraliza a comunicação com o backend — se o
// endereço da API mudar no futuro, só precisamos editar aqui.

const API_BASE_URL = "http://localhost:8000";

export async function sendMessage(message: string): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });

  if (!response.ok) {
    throw new Error(`Erro na API: ${response.status}`);
  }

  const data = await response.json();
  return data.response;
}

export async function getStatus(): Promise<{ agent_name: string; status: string }> {
  const response = await fetch(`${API_BASE_URL}/api/status`);
  return response.json();
}