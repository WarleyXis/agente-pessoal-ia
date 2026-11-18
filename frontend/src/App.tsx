import { useEffect, useState, type FormEvent } from 'react';
import { api, getStatus, sendMessage, type ChatResult, type Report } from './api';
import { Reports } from './Reports';
import { Microphone } from './Microphone';
import { captureWindow, speakLocally, uploadMedia } from './media';
import './App.css';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

function App() {
  const [name, setName] = useState('Atlas');
  const [online, setOnline] = useState(false);
  const [model, setModel] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');
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
      setOnline(true);
    }).catch(() => setError('Backend indisponível. Inicie o Atlas e recarregue a página.'));
    api<string[]>('/projects').then((items) => {
      setProjects(items);
      setProject(items[0] || '');
    }).catch((failure: Error) => setError(failure.message));
    api<Report[]>('/reports').then(setReports).catch((failure: Error) => setError(failure.message));
  }, []);

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

  function show(result: ChatResult) {
    if ('approval' in result) {
      setApproval(result.approval);
    } else {
      setMessages((previous) => [...previous, { role: 'assistant', content: result.response }]);
      if (speak && !speakLocally(result.response)) setError('Nenhuma voz local em português do Brasil está disponível no navegador.');
    }
  }

  async function createReview(target: string, includeTests: boolean) {
    const report = await api<Report>('/reports', { project: target, include_tests: includeTests });
    record(report);
    return report;
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    const message = input.trim();
    if (!message || busy || approval || listening) return;
    setMessages((previous) => [...previous, { role: 'user', content: message }]);
    setInput('');
    const lower = message.toLocaleLowerCase('pt-BR');
    const matches = projects.filter((item) => lower.includes(item.toLocaleLowerCase('pt-BR')));
    const target = matches.length === 1 && /revis|relat[oó]rio/.test(lower) ? matches[0] : '';
    void action(target ? 'Consultando projeto' : 'Consultando modelo', async () => {
      if (target) {
        await createReview(target, /teste|pytest/.test(lower));
        show({ response: `Relatório de ${target} disponível no painel de projetos.` });
        return;
      }
      show(await sendMessage(message));
    });
  }

  return <main className="dashboard">
    <header className="dashboard-header">
      <div><h1>{name}</h1><p>Assistente pessoal local</p></div>
      <p className="status" role="status"><span />{(listening ? 'Ouvindo' : busy) || (approval ? 'Aguardando sua decisão' : online ? 'Painel conectado' : 'Sem conexão')}{model && <small>{model}</small>}</p>
    </header>
    {error && <p className="error" role="alert">{error}</p>}
    <div className="layout">
      <section className="card chat" aria-label="Conversa">
        <h2>Conversa</h2>
        <div className="messages" aria-live="polite">
          {!messages.length && <p className="muted">Escreva um pedido para começar.</p>}
          {messages.map((message, index) => <article key={index} className={message.role}>
            <strong>{message.role === 'user' ? 'Você' : name}</strong>
            <p>{message.content}</p>
          </article>)}
        </div>
        {approval && <section className="approval">
          <h3>{approval.tool}</h3>
          <pre>{JSON.stringify(approval.arguments, null, 2)}</pre>
          <div className="actions">{[true, false].map((approved) =>
            <button key={String(approved)} disabled={!!busy} onClick={() => {
              void action('Processando decisão', async () => {
                setApproval(null);
                show(await api<ChatResult>(`/approvals/${approval.id}`, { approved }));
              });
            }}>{approved ? 'Aprovar' : 'Recusar'}</button>)}</div>
        </section>}
        <form className="composer" onSubmit={submit}>
          <input aria-label="Pedido ao Atlas" placeholder="Digite seu pedido" value={input} onChange={(event) => setInput(event.target.value)} />
          <button disabled={!input.trim() || !!busy || !!approval || listening}>Enviar</button>
        </form>
        <div className="actions media">
          <Microphone disabled={!!busy || !!approval} onError={setError} onState={setListening} onAudio={(blob) => {
            void action('Transcrevendo', async () => {
              setInput((await uploadMedia<{ text: string }>('/transcribe', blob)).text);
            });
          }} />
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
            if (!event.target.checked) window.speechSynthesis?.cancel();
          }} /> Ler respostas</label>
          {speak && <button onClick={() => window.speechSynthesis?.cancel()}>Parar voz</button>}
        </div>
      </section>
      <section className="card" aria-label="Projetos">
        <h2>Projetos</h2>
        {projects.length > 0 ? <form onSubmit={(event) => {
          event.preventDefault();
          void action('Consultando projeto', async () => { await createReview(project, withTests); });
        }}>
          <label htmlFor="project">Projeto</label>
          <select id="project" value={project} onChange={(event) => setProject(event.target.value)}>
            {projects.map((item) => <option key={item}>{item}</option>)}
          </select>
          <label className="checkbox"><input type="checkbox" checked={withTests} onChange={(event) => setWithTests(event.target.checked)} /> Incluir testes</label>
          <button disabled={!!busy}>Gerar relatório</button>
        </form> : <p className="muted">Cadastre seus projetos em <code>data/projects.json</code>.</p>}
        <Reports reports={reports} busy={busy} decide={(report, approved) => {
          void action(approved ? 'Executando testes' : 'Registrando recusa', async () => {
            record(await api<Report>(`/reports/${report.id}/decision`, { approved }));
          });
        }} />
      </section>
    </div>
  </main>;
}

export default App;
