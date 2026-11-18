# Atlas

Assistente pessoal que roda no seu computador, com conversa em português, consultas à web e ações locais mediante aprovação no painel. Os dados da instalação ficam em `data/` e a configuração fica em `.env`.

## Instalação no Windows

Use Git, Python 3.12, Node.js 24 e Ollama. Abra o PowerShell na raiz do repositório.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
ollama pull qwen3:4b
ollama pull moondream
npm --prefix frontend ci
npm --prefix frontend run build
.\.venv\Scripts\python.exe -m uvicorn backend.api.app:app --host 127.0.0.1 --port 8000
```

Abra [Atlas local](http://localhost:8000). Mude `AGENT_NAME` no `.env` para personalizar o nome. Use `ollama list` para verificar os modelos instalados e [o estado da API](http://localhost:8000/api/status) para verificar o nome e o modelo configurado. O estado da API indica que o backend iniciou. O primeiro pedido ao chat testa a conexão com o modelo.

Para desenvolvimento do painel, rode `npm --prefix frontend run dev` e abra [o servidor do frontend](http://localhost:5173). Para as ferramentas de navegação web, instale também o navegador com `.\.venv\Scripts\python.exe -m playwright install chromium`.

## Aplicativo desktop no Windows

Abra o Ollama e execute `.\InstalarAtlasDesktop.cmd` no PowerShell a partir da pasta do Atlas. O instalador baixa o modelo de conversa **Qwen3 4B** e a voz brasileira **Faber** do Piper, instala a janela desktop e gera a interface. Depois, dê dois cliques em **AbrirAtlas.cmd**. A janela usa o WebView2 do Windows e abre sem precisar de uma janela do navegador. Autorize o microfone quando o Windows ou a janela pedir.

Se o Atlas pedir o runtime, instale o [Microsoft Edge WebView2](https://developer.microsoft.com/microsoft-edge/webview2/). O comando de instalação seleciona o Qwen3 e a voz Faber para esta cópia do Atlas; os demais ajustes do `.env` e os dados locais são preservados.

Para abrir a janela ao entrar no Windows, execute `.\ConfigurarInicializacaoAtlas.cmd ativar-janela`. A opção de iniciar só o painel local segue abaixo.

## Iniciar junto com o Windows

Depois de instalar as dependências e gerar o painel, execute uma vez na pasta do Atlas:

```powershell
.\ConfigurarInicializacaoAtlas.cmd
```

O atalho **Atlas** é adicionado à pasta de inicialização da sua conta, sem precisar de administrador. Ao entrar no Windows, o Atlas inicia em segundo plano. Abra [o painel local](http://localhost:8000) no navegador quando quiser usar. O servidor escuta apenas em `127.0.0.1`.

O chat e a visão usam o Ollama. O instalador oficial do Ollama para Windows registra sua própria inicialização com a sessão. Se você desativou essa opção, reative o Ollama em **Configurações → Aplicativos → Inicialização** para ter os modelos disponíveis ao entrar. Se o painel não abrir, confira `data/inicializacao.log` e se a porta 8000 está ocupada.

Para desativar a inicialização do Atlas:

```powershell
.\ConfigurarInicializacaoAtlas.cmd desativar
```

Esse comando remove o atalho de futuros logins. Se mudar a pasta do Atlas, execute a ativação novamente no novo local.

## Web e arquivos

No painel **Web e arquivos**, cole o endereço HTTPS de uma página pública ou prepare uma nota. O Atlas mostra o endereço antes da consulta e, para uma gravação, mostra a operação, o caminho completo e o texto a salvar. A recusa encerra a ação. Esses controles funcionam com o backend ligado, mesmo com o Ollama desligado. Você também pode solicitar as ações em linguagem natural pelo chat.

- Configure `WEB_HOSTS` no `.env` com uma lista de domínios públicos confiáveis separados por vírgula. A consulta extrai texto e informa a fonte. Sites privados, páginas que exigem login e páginas dependentes de JavaScript podem precisar de uma integração própria.
- Use `NOTES_DIRECTORY` no `.env` para escolher a pasta de notas. O padrão é `data/notas`. O Atlas pode criar arquivos `.txt` ou `.md` e acrescentar texto aos que já existem nessa pasta. Criar uma nota com nome já existente preserva o arquivo.
- Em Windows, o chat também pode pedir autorização para abrir aplicativos permitidos, clicar e digitar. Revise a ação no painel antes de aprová-la.

Relatórios de Git e pytest são uma ferramenta opcional. Para habilitá-la, cadastre projetos confiáveis em `data/projects.json` no formato `{"Projeto de exemplo":{"path":"C:/Projetos/Exemplo"}}`. O campo opcional `python` aponta para o interpretador do projeto. O pytest roda na raiz cadastrada após aprovação.

## Microfone, voz e janela

- Clique em **Falar com o Atlas** e faça uma pergunta. Depois de uma pausa na fala (ou ao clicar em **Enviar fala**), o Atlas transcreve, envia o pedido e responde por voz. Clique em **Falar com o Atlas** novamente para outro turno. **Cancelar** descarta a gravação. A primeira transcrição pode baixar o modelo Whisper `small`, que roda localmente.
- A esfera acompanha o ponteiro e reage ao volume do microfone e da resposta em áudio. A síntese usa o modelo neural pt-BR do Piper. Instale a voz pela configuração desktop para obter áudio também no painel web. A resposta sempre fica visível no chat.
- Use **Parar voz** para interromper a leitura. **Ler também respostas digitadas** ativa a voz para pedidos de texto. As ações que exigem autorização continuam aguardando sua decisão no painel.
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
