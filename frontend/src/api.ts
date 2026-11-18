export async function api<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(`/api${path}`, body === undefined ? undefined : {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const detail: unknown = payload?.detail;
    throw new Error(typeof detail === 'string' ? detail : 'O Atlas não conseguiu concluir a solicitação.');
  }
  return response.json();
}

export interface OllamaTiming {
  model: string;
  load_ms: number;
  prompt_ms: number;
  generation_ms: number;
  calls: number;
}

export type ChatResult =
  & { ollama_timing?: OllamaTiming }
  & ({ response: string } | { approval: { id: string; tool: string; arguments: Record<string, unknown> } });

export function sendMessage(message: string, spoken = false, fast = false) {
  return api<ChatResult>('/chat', { message, spoken, fast });
}

export function getStatus() {
  return api<{ agent_name: string; status: string; model: string; fast_model: string }>('/status');
}

export interface CommandResult {
  state: string;
  command?: string[];
  exit_code?: number;
  output?: string;
}

export interface Report {
  id: string;
  project: string;
  path: string;
  created_at: string;
  git: { state: 'no_git' } | { status: CommandResult; commits: CommandResult };
  tests: CommandResult;
}
