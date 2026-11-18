import { useEffect, useRef, useState, type FormEvent } from 'react';
import { api, getStatus, sendMessage, type ChatResult, type OllamaTiming, type Report } from './api';
import { Reports } from './Reports';
import { PersonalActions } from './PersonalActions';
import { Microphone } from './Microphone';
import { captureWindow, uploadMedia } from './media';
import { useVoice } from './useVoice';
import { VoiceOrb } from './VoiceOrb';
import './App.css';

const actionLabels: Record<string, string> = {
  open_url: 'Consultar página pública',
  save_note: 'Gravar nota no computador',
  open_application: 'Abrir aplicativo',
  click_at: 'Clicar no computador',
  type_text: 'Digitar no computador',
  describe_screen: 'Capturar a tela',
  run_tests: 'Executar testes',
};

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

function App() {
  const [name, setName] = useState('Atlas');
  const [online, setOnline] = useState(false);
  const [model, setModel] = useState('');
  const [fastModel, setFastModel] = useState('');
  const [fastVoice, setFastVoice] = useState(() => localStorage.getItem('atlas-fast-voice') === 'true');
  const [messages, setMessages] = useState<Message[]>([]);
  const messageList = useRef<HTMLDivElement>(null);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');
  const voice = useVoice(setError);
  const spokenApproval = useRef(false);
  const [voiceTimes, setVoiceTimes] = useState<{ recognition: number; reply?: number; playback?: number; ollama?: OllamaTiming } | null>(null);
  const [listening, setListening] = useState(false);
  const [speak, setSpeak] = useState(false);
  const [approval, setApproval] = useState<Extract<ChatResult, { approval: unknown }>['approval'] | null>(null);
  const [projects, setProjects] = useState<string[]>([]);
  const [project, setProject] = useState('');
  const [withTests, setWithTests] = useState(false);
  const [reports, setReports] = useState<Report[]>([]);

  useEffect(() => {
    getStatus().then((status) => {
      setName(status.agent_name);
      setModel(status.model);
      setFastModel(status.fast_model);
      setOnline(true);
    }).catch(() => setError('Backend indisponível. Inicie o Atlas e recarregue a página.'));
    api<string[]>('/projects').then((items) => {
      setProjects(items);
      setProject(items[0] || '');
    }).catch((failure: Error) => setError(failure.message));
    api<Report[]>('/reports').then(setReports).catch((failure: Error) => setError(failure.message));
  }, []);

  useEffect(() => {
    if (messageList.current) messageList.current.scrollTop = messageList.current.scrollHeight;
  }, [messages]);

  function record(report: Report) {
    setReports((previous) => {
      const found = previous.some((item) => item.id === report.id);
      return found ? previous.map((item) => item.id === report.id ? report : item) : [report, ...previous];
    });
  }

  async function action(label: string, operation: () => Promise<void>) {
    setBusy(label);
    setError('');
    try {
      await operation();
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : 'Ocorreu uma falha no Atlas.');
    } finally {
      setBusy('');
    }
  }

  function show(result: ChatResult, spoken = speak, reportPlayback?: (elapsed: number) => void) {
    if ('approval' in result) {
      setApproval(result.approval);
      spokenApproval.current = spoken;
      if (spoken) void voice.play('Preciso da sua autorização. Confira a ação no painel.', reportPlayback);
    } else {
      setMessages((previous) => [...previous, { role: 'assistant', content: result.response }]);
      if (spoken) void voice.play(result.response, reportPlayback);
    }
  }

  async function createReview(target: string, includeTests: boolean) {
    const report = await api<Report>('/reports', { project: target, include_tests: includeTests });
    record(report);
    return report;
  }

  async function sendPrompt(message: string, spoken: boolean, recognition?: number) {
    const started = performance.now();
    function deliver(result: ChatResult) {
      const reply = performance.now() - started;
      if (recognition !== undefined) {
        const timing = { recognition, reply, ollama: result.ollama_timing };
        setVoiceTimes(timing);
        show(result, spoken, (playback) => setVoiceTimes({ ...timing, playback }));
      } else {
        show(result, spoken);
      }
    }
    setMessages((previous) => [...previous, { role: 'user', content: message }]);
    setInput('');
    const lower = message.toLocaleLowerCase('pt-BR');
    const matches = projects.filter((item) => lower.includes(item.toLocaleLowerCase('pt-BR')));
    const target = matches.length === 1 && /revis|relat[oó]rio/.test(lower) ? matches[0] : '';
    setBusy(target ? 'Consultando projeto' : 'Processando pedido');
    if (target) {
      await createReview(target, /teste|pytest/.test(lower));
      deliver({ response: `Relatório de ${target} disponível no painel de projetos.` });
      return;
    }
    deliver(await sendMessage(message, spoken, recognition !== undefined && fastVoice));
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    const message = input.trim();
    if (!message || busy || approval || listening) return;
    if (speak) voice.prepare();
    void action('Processando pedido', () => sendPrompt(message, speak));
  }

  const voiceState = listening ? 'listening' : approval ? 'approval' :
    busy || voice.preparing ? 'thinking' : voice.speaking ? 'speaking' : 'idle';
  const voiceStatus = listening ? 'Ouvindo você' : approval ? 'Aguardando sua aprovação' :
    busy || (voice.preparing ? 'Preparando áudio' : voice.speaking ? 'Atlas falando' : 'Pronto para conversar');

  return <main className="dashboard">
    <header className="dashboard-header">
      <div className="brand"><span className="brand-mark" aria-hidden="true" /><h1>{name}</h1></div>
      <div className="connection"><span className="status" data-online={online}><span />{online ? 'Conectado' : 'Sem conexão'}</span>{model && <small>{model}</small>}</div>
    </header>
    {error && <p className="error" role="alert">{error}</p>}
    <div className="layout">
      <section className="card voice-console" aria-label="Conversa por voz">
        <VoiceOrb state={voiceState} level={voice.level} />
        <div className="voice-guide">
          <h2 role="status">{online ? voiceStatus : 'Aguardando conexão'}</h2>
          <p>Fale naturalmente. Uma pausa envia sua pergunta.</p>
          <div className="actions voice-controls">
            <Microphone disabled={!online || !!busy || !!approval} onError={setError}
              audioContext={() => { voice.stop(); return voice.prepare(); }}
              onLevel={voice.setLevel} onState={setListening} onAudio={(blob) => {
                void action('Transcrevendo sua fala', async () => {
                  setVoiceTimes(null);
                  const started = performance.now();
                  const { text } = await uploadMedia<{ text: string }>('/transcribe', blob);
                  const recognition = performance.now() - started;
                  setVoiceTimes({ recognition });
                  await sendPrompt(text, true, recognition);
                });
              }} />
            {(voice.speaking || voice.preparing) && <button type="button" onClick={voice.stop}>Parar voz</button>}
          </div>
          {fastModel && <label className="checkbox">
            <input type="checkbox" checked={fastVoice} onChange={(event) => {
              setFastVoice(event.target.checked);
              localStorage.setItem('atlas-fast-voice', String(event.target.checked));
            }} disabled={listening || !!busy} /> Voz rápida · {fastModel}
          </label>}
          {voiceTimes && <p className="voice-times">
            Transcrição {(voiceTimes.recognition / 1000).toLocaleString('pt-BR', { maximumFractionDigits: 1 })} s
            {voiceTimes.reply !== undefined && ` · Resposta ${(voiceTimes.reply / 1000).toLocaleString('pt-BR', { maximumFractionDigits: 1 })} s`}
            {voiceTimes.playback !== undefined && ` · Áudio ${(voiceTimes.playback / 1000).toLocaleString('pt-BR', { maximumFractionDigits: 1 })} s`}
          </p>}
          {voiceTimes?.ollama && <p className="voice-times">
            Modelo {voiceTimes.ollama.model}
            {' · Carregamento '}{(voiceTimes.ollama.load_ms / 1000).toLocaleString('pt-BR', { maximumFractionDigits: 1 })} s
            {' · Contexto '}{(voiceTimes.ollama.prompt_ms / 1000).toLocaleString('pt-BR', { maximumFractionDigits: 1 })} s
            {' · Geração '}{(voiceTimes.ollama.generation_ms / 1000).toLocaleString('pt-BR', { maximumFractionDigits: 1 })} s
            {' · '}{voiceTimes.ollama.calls} {voiceTimes.ollama.calls === 1 ? 'consulta' : 'consultas'}
          </p>}
        </div>
      </section>
      <section className="card chat" aria-label="Conversa">
        <h2>Conversa</h2>
        <div className="messages" ref={messageList} aria-live="polite">
          {!messages.length && <p className="muted">Escreva um pedido para começar.</p>}
          {messages.map((message, index) => <article key={index} className={message.role}>
            <strong>{message.role === 'user' ? 'Você' : name}</strong>
            <p>{message.content}</p>
          </article>)}
        </div>
        {approval && <section className="approval">
          <h3>{actionLabels[approval.tool] || approval.tool}</h3>
          {approval.tool === 'save_note' ? <>
            <p>{approval.arguments.mode === 'append' ? 'Acrescentar texto' : 'Criar arquivo'} em <strong>{String(approval.arguments.path)}</strong></p>
            <pre>{String(approval.arguments.content)}</pre>
          </> : <pre>{approval.tool === 'open_url'
            ? String(approval.arguments.url) : JSON.stringify(approval.arguments, null, 2)}</pre>}
          <div className="actions">{[true, false].map((approved) =>
            <button key={String(approved)} disabled={!!busy} onClick={() => {
              if (spokenApproval.current) voice.prepare();
              voice.stop();
              void action('Processando decisão', async () => {
                setApproval(null);
                show(await api<ChatResult>(`/approvals/${approval.id}`, { approved }), spokenApproval.current);
              });
            }}>{approved ? 'Aprovar' : 'Recusar'}</button>)}</div>
        </section>}
        <form className="composer" onSubmit={submit}>
          <input aria-label="Pedido ao Atlas" placeholder="Digite seu pedido" value={input} onChange={(event) => setInput(event.target.value)} />
          <button disabled={!input.trim() || !!busy || !!approval || listening}>Enviar</button>
        </form>
        <div className="actions media">
          <button disabled={!!busy || !!approval || listening} onClick={() => {
            const question = input.trim() || 'Descreva o que está visível nesta janela.';
            void action('Lendo janela', async () => {
              const image = await captureWindow();
              const result = await uploadMedia<{ response: string }>(`/vision?question=${encodeURIComponent(question)}`, image);
              setMessages((previous) => [...previous, { role: 'user', content: question }]);
              setInput('');
              show(result);
            });
          }}>Ler janela ou aba</button>
          <label className="checkbox"><input type="checkbox" checked={speak} onChange={(event) => {
            setSpeak(event.target.checked);
            if (event.target.checked) voice.prepare();
            else voice.stop();
          }} /> Ler também respostas digitadas</label>
        </div>
      </section>
      <aside className="side-panel">
        <PersonalActions disabled={!online || !!busy || !!approval || listening} run={(request) => {
          void action('Preparando ação', async () => show(await api<ChatResult>('/actions', request)));
        }} />
        {(projects.length > 0 || reports.length > 0) && <details className="card" aria-label="Projetos">
          <summary>Relatórios de projetos</summary>
          {projects.length > 0 ? <form onSubmit={(event) => {
            event.preventDefault();
            void action('Consultando projeto', async () => { await createReview(project, withTests); });
          }}>
            <label htmlFor="project">Projeto</label>
            <select id="project" value={project} onChange={(event) => setProject(event.target.value)}>
              {projects.map((item) => <option key={item}>{item}</option>)}
            </select>
            <label className="checkbox"><input type="checkbox" checked={withTests} onChange={(event) => setWithTests(event.target.checked)} /> Incluir testes</label>
            <button disabled={!!busy || !!approval || listening}>Gerar relatório</button>
          </form> : <p className="muted">Cadastre seus projetos em <code>data/projects.json</code>.</p>}
          <Reports reports={reports} busy={busy || (approval || listening ? 'Aguardando' : '')} decide={(report, approved) => {
            void action(approved ? 'Executando testes' : 'Registrando recusa', async () => {
              record(await api<Report>(`/reports/${report.id}/decision`, { approved }));
            });
          }} />
        </details>}
      </aside>
    </div>
  </main>;
}

export default App;
