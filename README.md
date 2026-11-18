# Atlas

Assistente pessoal que roda localmente, com chat em português, aprovações no painel e relatórios de projetos. Os dados da instalação ficam em `data/` e a configuração fica em `.env`.

## Instalação no Windows

Use Git, Python 3.12, Node.js 24 e Ollama. Abra o PowerShell na raiz do repositório.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
ollama pull qwen2.5:3b
ollama pull moondream
npm --prefix frontend ci
npm --prefix frontend run build
.\.venv\Scripts\python.exe -m uvicorn backend.api.app:app --host 127.0.0.1 --port 8000
```

Abra [Atlas local](http://localhost:8000). Mude `AGENT_NAME` no `.env` para personalizar o nome. Use `ollama list` para verificar os modelos instalados e [o estado da API](http://localhost:8000/api/status) para verificar o nome e o modelo configurado. O estado da API indica que o backend iniciou. O primeiro pedido ao chat testa a conexão com o modelo.

Para desenvolvimento do painel, rode `npm --prefix frontend run dev` e abra [o servidor do frontend](http://localhost:5173). Para as ferramentas de navegação web, instale também o navegador com `.\.venv\Scripts\python.exe -m playwright install chromium`.

## Projetos e relatórios

Crie `data/projects.json` com as pastas de projetos confiáveis deste computador. Use caminhos absolutos. O campo `python` é opcional e deve apontar para o Python do ambiente desse projeto. Sem ele, o Atlas usa o próprio Python.

```json
{
  "Finance Hub": {
    "path": "C:/Projetos/FinanceHub",
    "python": "C:/Projetos/FinanceHub/.venv/Scripts/python.exe"
  }
}
```

No painel **Projetos**, selecione o projeto e gere um relatório. Pelo chat do painel, você também pode pedir “Revise meu Finance Hub e me diga se os testes passaram”. O Atlas consulta o Git local quando há metadados do repositório, mostra o comando antes de rodar pytest e guarda o relatório no SQLite. O pytest roda na raiz cadastrada. Use a opção de testes com projetos cujo código você confia. O relatório também funciona para pastas sem Git.

## Microfone, voz e janela

- Escolha **Microfone**, fale e pressione **Transcrever gravação**. Confira o texto antes de enviar. A primeira transcrição pode baixar o modelo Whisper `small`, que roda localmente nas chamadas seguintes.
- Ative **Ler respostas** para usar uma voz local em português do Brasil instalada no Windows e disponível no navegador. Use **Parar voz** para interromper a leitura.
- Escolha **Ler janela ou aba**, selecione uma janela ou aba no navegador e deixe o Ollama analisar a captura. Se quiser fazer uma pergunta específica, escreva-a antes de clicar. A captura é pontual e a sessão de compartilhamento é encerrada logo depois.
- Os modos de terminal continuam disponíveis com `python -m backend.main` e `python -m backend.voice_main`, usando o Python do ambiente virtual.

## Validação

```powershell
.\.venv\Scripts\python.exe -m pytest -q
npm --prefix frontend run lint
npm --prefix frontend run build
```

No Windows, confira chat com o Ollama ligado e desligado, aprovação e recusa de uma ferramenta, relatório com Git e sem Git, reabertura do histórico e retorno dos testes. Em Edge ou Chrome, valide permissão e cancelamento do microfone, transcrição em português, interrupção da voz e captura de uma janela. App externo, foco e digitação precisam ser conferidos na sessão gráfica real.

## Voltar à Fase 14

A referência [backup/atlas-fase-14](https://github.com/WarleyXis/agente-pessoal-ia/tree/backup/atlas-fase-14) aponta para o commit `cc47222`. Para testar a versão anterior sem tocar na pasta de trabalho atual, crie outro checkout com `git worktree add --detach ../atlas-fase-14 origin/backup/atlas-fase-14` após `git fetch origin`. Cada pasta pode manter seu próprio `.env` e `data/`.
