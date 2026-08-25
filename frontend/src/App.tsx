// Tela de chat simples: uma lista de mensagens e um campo para
// digitar. Ainda sem visual "futurista" (isso vem numa fase bem
// mais à frente) — o objetivo agora é só provar que o frontend
// consegue conversar com o agente através da API.

import { useEffect, useState } from "react";
import { getStatus, sendMessage } from "./api";

interface Message {
  role: "user" | "assistant";
  content: string;
}

function App() {
  const [agentName, setAgentName] = useState("Agente");
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Busca o nome do agente configurado no .env assim que a página
    // carrega — reforça que o nome nunca fica fixo em lugar nenhum,
    // nem aqui no frontend.
    getStatus()
      .then((status) => setAgentName(status.agent_name))
      .catch(() => {});
  }, []);

  async function handleSend() {
    const texto = input.trim();
    if (!texto || loading) return;

    // Mostra a mensagem do usuário na tela imediatamente, sem
    // esperar a resposta do agente — deixa a interface mais ágil.
    setMessages((prev) => [...prev, { role: "user", content: texto }]);
    setInput("");
    setLoading(true);

    try {
      const resposta = await sendMessage(texto);
      setMessages((prev) => [...prev, { role: "assistant", content: resposta }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Erro ao falar com o agente. O backend está rodando?" },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") handleSend();
  }

  return (
    <div style={{ maxWidth: 600, margin: "0 auto", padding: 20, fontFamily: "sans-serif" }}>
      <h1>{agentName}</h1>
      <div style={{ border: "1px solid #ccc", borderRadius: 8, padding: 12, minHeight: 300, marginBottom: 12 }}>
        {messages.map((msg, i) => (
          <p key={i}>
            <strong>{msg.role === "user" ? "Você" : agentName}:</strong> {msg.content}
          </p>
        ))}
        {loading && <p><em>Pensando...</em></p>}
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        <input
          style={{ flex: 1, padding: 8 }}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Digite sua mensagem..."
        />
        <button onClick={handleSend} disabled={loading}>Enviar</button>
      </div>
    </div>
  );
}

export default App;