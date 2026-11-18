import type { CommandResult, Report } from './api';

const states: Record<string, string> = {
  pending: 'Aguardando sua aprovação',
  running: 'Executando testes',
  passed: 'Concluído com sucesso',
  failed: 'Execução retornou erro',
  timeout: 'Tempo limite atingido',
  unavailable: 'Comando indisponível',
  interrupted: 'Interrompido pelo reinício do Atlas',
  declined: 'Execução recusada',
  not_requested: 'Testes não solicitados',
};

function Result({ result }: { result: CommandResult }) {
  return <>
    <p>{states[result.state]}{result.exit_code !== undefined && ` · Código ${result.exit_code}`}</p>
    {result.output && <pre>{result.output}</pre>}
  </>;
}

export function Reports({ reports, busy, decide }: {
  reports: Report[];
  busy: string;
  decide: (report: Report, approved: boolean) => void;
}) {
  return <div className="reports">
    {reports.length === 0 && <p className="muted">Os relatórios de projeto aparecerão aqui.</p>}
    {reports.map((report, index) => (
      <details key={report.id} open={index === 0 || report.tests.state === 'pending'}>
        <summary>{report.project} <small>{new Date(report.created_at).toLocaleString('pt-BR')}</small></summary>
        <p className="muted path">{report.path}</p>
        <h3>Git</h3>
        {'state' in report.git ? <p>A pasta cadastrada não tem metadados do Git.</p> : <>
          <Result result={report.git.status} />
          <Result result={report.git.commits} />
        </>}
        <h3>Testes</h3>
        <Result result={report.tests} />
        {report.tests.state === 'pending' && <>
          <pre>{report.tests.command?.join(' ')}</pre>
          <div className="actions">
            <button disabled={!!busy} onClick={() => decide(report, true)}>Executar testes</button>
            <button disabled={!!busy} onClick={() => decide(report, false)}>Recusar</button>
          </div>
        </>}
      </details>
    ))}
  </div>;
}
