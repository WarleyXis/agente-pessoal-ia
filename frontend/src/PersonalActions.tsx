import { useState } from 'react';

export type PersonalAction =
  | { tool: 'open_url'; arguments: { url: string } }
  | { tool: 'save_note'; arguments: { filename: string; content: string; mode: 'create' | 'append' } };

export function PersonalActions({ disabled, run }: {
  disabled: boolean;
  run: (request: PersonalAction) => void;
}) {
  const [url, setUrl] = useState('');
  const [filename, setFilename] = useState('');
  const [content, setContent] = useState('');
  const [mode, setMode] = useState<'create' | 'append'>('create');

  return <section className="card personal-actions" aria-label="Web e arquivos">
    <h2>Web e arquivos</h2>
    <form onSubmit={(event) => {
      event.preventDefault();
      run({ tool: 'open_url', arguments: { url: url.trim() } });
    }}>
      <label htmlFor="page-url">Página pública</label>
      <input id="page-url" placeholder="https://pt.wikipedia.org/…" value={url} maxLength={2048}
        onChange={(event) => setUrl(event.target.value)} required />
      <button disabled={disabled || !url.trim()}>Consultar página</button>
    </form>
    <form onSubmit={(event) => {
      event.preventDefault();
      run({ tool: 'save_note', arguments: { filename: filename.trim(), content, mode } });
    }}>
      <label htmlFor="note-filename">Nome da nota</label>
      <input id="note-filename" placeholder="Minha nota.md" maxLength={79} value={filename}
        onChange={(event) => setFilename(event.target.value)} required />
      <label htmlFor="note-mode">Alteração</label>
      <select id="note-mode" value={mode} onChange={(event) => setMode(event.target.value === 'append' ? 'append' : 'create')}>
        <option value="create">Criar nota</option>
        <option value="append">Acrescentar texto a uma nota</option>
      </select>
      <label htmlFor="note-content">Texto da nota</label>
      <textarea id="note-content" rows={4} value={content} maxLength={10000}
        onChange={(event) => setContent(event.target.value)} required />
      <button disabled={disabled || !filename.trim() || !content.trim()}>Revisar gravação</button>
    </form>
  </section>;
}
