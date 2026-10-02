import { useEffect, useState } from 'react';

const STAGES = [
  { id: 'requirement_case', label: 'Requirement Case', icon: '🎯' },
  { id: 'international_research', label: 'International Research', icon: '🔍' },
  { id: 'standardized_methodology', label: 'Standardized Methodology', icon: '📐' },
  { id: 'scad_input_analysis', label: 'SCAD Input Analysis', icon: '📥' },
  { id: 'clarification', label: 'Clarification / Q&A', icon: '❓' },
  { id: 'indicator_development', label: 'Indicator Development', icon: '📊' },
  { id: 'scad_methodology', label: 'SCAD Methodology', icon: '📄' },
  { id: 'compliance', label: 'Compliance / QA', icon: '✅' },
  { id: 'gap_assessment', label: 'Gap Assessment', icon: '🧩' },
];

const DOC_STAGES = [
  'international_research',
  'standardized_methodology',
  'scad_methodology',
  'gap_assessment',
];

const STATUS_COLOR = {
  PENDING: 'bg-slate-500',
  RUNNING: 'bg-blue-500 animate-pulse',
  COMPLETED: 'bg-emerald-500',
  WAITING_FOR_HUMAN: 'bg-amber-400 animate-pulse',
  BLOCKED: 'bg-red-500',
  FAILED: 'bg-red-600',
  SKIPPED: 'bg-slate-600',
};

const EVENT_TO_STATUS = {
  'stage.started': 'RUNNING',
  'stage.completed': 'COMPLETED',
  'stage.skipped': 'SKIPPED',
  'stage.blocked': 'BLOCKED',
  'agent.failed': 'FAILED',
  'approval.requested': 'WAITING_FOR_HUMAN',
  'approval.granted': 'COMPLETED',
  'approval.rejected': 'BLOCKED',
};

const EVENT_LABEL = {
  'stage.started': 'Agent started',
  'stage.completed': 'Agent completed',
  'stage.skipped': 'Stage skipped',
  'stage.blocked': 'Stage blocked',
  'agent.failed': 'Agent failed',
  'approval.requested': 'Approval requested',
  'approval.granted': 'Approval granted',
  'approval.rejected': 'Approval rejected',
  'workflow.completed': 'Workflow completed',
};

function wsUrl() {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${proto}//${window.location.host}/ws/dashboard`;
}

function api(path, options) {
  return fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
}

function MethodologyDoc({ title, sections }) {
  if (!sections?.length) return null;
  return (
    <div className="dash-fade-in rounded-xl border border-slate-800 bg-slate-900 p-5">
      <h3 className="mb-3 text-lg font-semibold text-slate-100">{title}</h3>
      <div className="max-h-96 space-y-3 overflow-y-auto pr-1">
        {sections.map((s) => (
          <div key={s.number}>
            <div className="font-medium text-blue-300">
              {s.number}. {s.title}
            </div>
            <p className="whitespace-pre-wrap text-sm text-slate-300">{s.content}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function GapDoc({ gap }) {
  if (!gap) return null;
  return (
    <div className="dash-fade-in rounded-xl border border-slate-800 bg-slate-900 p-5">
      <h3 className="mb-3 text-lg font-semibold text-slate-100">Gap Assessment Report</h3>
      {gap.executive_summary && (
        <p className="mb-3 text-sm text-slate-300">{gap.executive_summary}</p>
      )}
      {gap.matrix?.length > 0 && (
        <table className="mb-3 w-full text-left text-sm">
          <thead>
            <tr className="text-slate-400">
              <th className="py-1 pr-3">Dimension</th>
              <th className="py-1 pr-3">Gap</th>
              <th className="py-1">Description</th>
            </tr>
          </thead>
          <tbody>
            {gap.matrix.map((m, i) => (
              <tr key={i} className="border-t border-slate-800">
                <td className="py-1 pr-3 font-medium">{m.dimension}</td>
                <td className="py-1 pr-3">
                  <span
                    className={`rounded px-1.5 py-0.5 text-xs ${
                      m.gap_level === 'Major'
                        ? 'bg-red-900/60 text-red-200'
                        : m.gap_level === 'Moderate'
                          ? 'bg-amber-900/60 text-amber-200'
                          : 'bg-emerald-900/60 text-emerald-200'
                    }`}
                  >
                    {m.gap_level}
                  </span>
                </td>
                <td className="py-1 text-slate-300">{m.description}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {gap.recommendations?.length > 0 && (
        <ul className="space-y-1 text-sm text-slate-300">
          {gap.recommendations.map((r, i) => (
            <li key={i} className="flex gap-2">
              <span className="text-slate-500">•</span>
              <span>{r}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function Dashboard() {
  const [connected, setConnected] = useState('connecting');
  const [cases, setCases] = useState({});
  const [feed, setFeed] = useState([]);
  const [documents, setDocuments] = useState({});
  const [busy, setBusy] = useState(false);

  async function approve(caseId, stageId, decision) {
    setBusy(true);
    try {
      await api(`/cases/${caseId}/stages/${stageId}/approve`, {
        method: 'POST',
        body: JSON.stringify({ decision }),
      });
    } finally {
      setBusy(false);
    }
  }

  async function advance(caseId) {
    setBusy(true);
    try {
      await api(`/cases/${caseId}/advance`, { method: 'POST', body: JSON.stringify({}) });
    } finally {
      setBusy(false);
    }
  }

  async function fetchOutput(caseId, stageId) {
    try {
      const res = await api(`/cases/${caseId}/stages/${stageId}/output`);
      const data = await res.json();
      setDocuments((prev) => ({
        ...prev,
        [caseId]: { ...(prev[caseId] || {}), [stageId]: data },
      }));
    } catch {
      // ignore
    }
  }

  useEffect(() => {
    let ws = null;
    let closed = false;
    let retry = 0;
    let timer = null;

    function handle(event) {
      const type = event.event_type;
      const caseId = event.session_id;
      const payload = event.payload || {};
      const stageId = payload.stage;
      const status = EVENT_TO_STATUS[type];

      if (status && stageId) {
        setCases((prev) => {
          const next = { ...prev };
          const caseObj = { ...(next[caseId] || { stages: {}, updatedAt: 0 }) };
          const stage = { ...(caseObj.stages[stageId] || {}) };
          stage.status = status;
          if (payload.agent) stage.agent = payload.agent;
          if (payload.purpose) stage.purpose = payload.purpose;
          if (payload.reasoning) stage.reasoning = payload.reasoning;
          if (payload.output_keys) stage.output_keys = payload.output_keys;
          caseObj.stages[stageId] = stage;
          caseObj.updatedAt = Date.now();
          next[caseId] = caseObj;
          return next;
        });
      }

      if (status === 'COMPLETED' && DOC_STAGES.includes(stageId)) {
        fetchOutput(caseId, stageId);
      }

      setFeed((prev) =>
        [
          {
            id: event.event_id,
            type,
            caseId,
            stageId,
            agent: payload.agent,
            ts: event.timestamp,
          },
          ...prev,
        ].slice(0, 250)
      );
    }

    function connect() {
      if (closed) return;
      setConnected('connecting');
      ws = new WebSocket(wsUrl());
      ws.onopen = () => {
        retry = 0;
        setConnected('connected');
      };
      ws.onmessage = (e) => {
        try {
          handle(JSON.parse(e.data));
        } catch {
          // ignore malformed frames
        }
      };
      ws.onclose = () => {
        if (closed) return;
        setConnected('reconnecting');
        timer = setTimeout(connect, Math.min(1000 * 2 ** retry, 10000));
        retry += 1;
      };
      ws.onerror = () => {};
    }

    connect();
    return () => {
      closed = true;
      if (timer) clearTimeout(timer);
      if (ws) ws.close();
    };
  }, []);

  const caseIds = Object.keys(cases).sort((a, b) => cases[b].updatedAt - cases[a].updatedAt);
  const activeCaseId = caseIds[0];
  const activeCase = activeCaseId ? cases[activeCaseId] : null;
  const activeDocs = activeCaseId ? documents[activeCaseId] || {} : {};

  const runningStage = activeCase
    ? STAGES.find((s) => activeCase.stages[s.id]?.status === 'RUNNING')
    : null;
  const waitingStages = activeCase
    ? STAGES.filter((s) => activeCase.stages[s.id]?.status === 'WAITING_FOR_HUMAN')
    : [];

  const reasoningStages = activeCase
    ? STAGES.filter((s) => activeCase.stages[s.id]?.reasoning?.length)
    : [];

  const standardized = activeDocs.standardized_methodology?.methodology;
  const scadMethodology = activeDocs.scad_methodology?.methodology;
  const gap = activeDocs.gap_assessment?.gap_assessment;

  return (
    <div className="min-h-screen bg-slate-950 p-6 font-sans text-slate-100">
      <header className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            SCAD Methodology Agentic Workflow
          </h1>
          <p className="text-sm text-slate-400">Live orchestration dashboard</p>
        </div>
        <div className="flex items-center gap-3">
          <span
            className={`inline-block h-3 w-3 rounded-full ${
              connected === 'connected'
                ? 'bg-emerald-400'
                : connected === 'connecting'
                  ? 'bg-amber-400'
                  : 'bg-red-500'
            }`}
          />
          <span className="text-sm uppercase tracking-wider text-slate-300">{connected}</span>
        </div>
      </header>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <section className="rounded-xl border border-slate-800 bg-slate-900 p-5 xl:col-span-2">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-sm uppercase tracking-widest text-slate-400">
              Workflow pipeline
            </h2>
            <div className="flex items-center gap-2">
              {activeCaseId && (
                <span className="rounded bg-slate-800 px-2 py-1 font-mono text-xs text-slate-300">
                  {activeCaseId}
                </span>
              )}
              {activeCaseId && (
                <button
                  onClick={() => advance(activeCaseId)}
                  disabled={busy}
                  className="rounded-lg bg-blue-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-blue-500 disabled:opacity-50"
                >
                  ▶ Advance workflow
                </button>
              )}
            </div>
          </div>

          {activeCase ? (
            <ol className="space-y-2">
              {STAGES.map((s) => {
                const st = activeCase.stages[s.id];
                const status = st?.status || 'PENDING';
                const isRunning = status === 'RUNNING';
                const isWaiting = status === 'WAITING_FOR_HUMAN';
                return (
                  <li
                    key={s.id}
                    className={`flex items-center gap-3 rounded-lg px-3 py-2.5 transition-colors ${
                      isRunning ? 'dash-running bg-slate-800' : 'bg-slate-800/50'
                    }`}
                  >
                    <span className="relative flex h-3 w-3 shrink-0">
                      {isRunning && (
                        <span className="dash-dot-ring absolute inline-flex h-full w-full rounded-full bg-blue-400" />
                      )}
                      <span
                        className={`relative inline-flex h-3 w-3 rounded-full ${
                          STATUS_COLOR[status] || 'bg-slate-500'
                        }`}
                      />
                    </span>
                    <span className="text-xl">{s.icon}</span>
                    <div className="min-w-0 flex-1">
                      <div className="font-medium">{s.label}</div>
                      {st?.purpose && (
                        <div className="truncate text-xs text-slate-400">{st.purpose}</div>
                      )}
                    </div>

                    {isWaiting ? (
                      <div className="flex shrink-0 items-center gap-1.5">
                        <button
                          onClick={() => approve(activeCaseId, s.id, 'approved')}
                          disabled={busy}
                          className="rounded bg-emerald-600 px-2.5 py-1 text-xs font-semibold text-white hover:bg-emerald-500 disabled:opacity-50"
                        >
                          ✓ Approve
                        </button>
                        <button
                          onClick={() => approve(activeCaseId, s.id, 'request_changes')}
                          disabled={busy}
                          className="rounded bg-amber-600 px-2.5 py-1 text-xs font-semibold text-white hover:bg-amber-500 disabled:opacity-50"
                        >
                          ↺ Changes
                        </button>
                        <button
                          onClick={() => approve(activeCaseId, s.id, 'rejected')}
                          disabled={busy}
                          className="rounded bg-red-600 px-2.5 py-1 text-xs font-semibold text-white hover:bg-red-500 disabled:opacity-50"
                        >
                          ✕ Reject
                        </button>
                      </div>
                    ) : (
                      <span className="text-xs uppercase tracking-wider text-slate-400">
                        {status.replace(/_/g, ' ')}
                      </span>
                    )}
                  </li>
                );
              })}
            </ol>
          ) : (
            <p className="text-slate-500">Waiting for the first request…</p>
          )}

          {activeCase && (
            <div className="mt-6">
              <h3 className="mb-3 text-sm uppercase tracking-widest text-slate-400">
                Chain of thought
              </h3>
              {reasoningStages.length > 0 ? (
                <div className="space-y-2">
                  {reasoningStages.map((s, idx) => (
                    <div
                      key={`${activeCaseId}-${s.id}`}
                      className="dash-slide-in rounded-lg bg-slate-800/70 p-3"
                      style={{ animationDelay: `${idx * 60}ms` }}
                    >
                      <div className="font-semibold text-blue-300">
                        {s.icon} {s.label}
                      </div>
                      <ul className="mt-1 space-y-1 text-sm text-slate-300">
                        {(activeCase.stages[s.id].reasoning || []).map((r, i) => (
                          <li key={i} className="flex gap-2">
                            <span className="text-slate-500">{i + 1}.</span>
                            <span>{r}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-500">
                  {runningStage
                    ? `${runningStage.icon} ${runningStage.label} is thinking…`
                    : 'No reasoning recorded yet.'}
                </p>
              )}
            </div>
          )}
        </section>

        <section className="flex max-h-screen flex-col rounded-xl border border-slate-800 bg-slate-900 p-5">
          <h2 className="mb-4 text-sm uppercase tracking-widest text-slate-400">
            Live activity
          </h2>
          <ul className="flex-1 space-y-2 overflow-y-auto pr-1">
            {feed.map((e) => (
              <li key={e.id} className="dash-fade-in rounded bg-slate-800/40 px-3 py-2 text-sm">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-medium">{EVENT_LABEL[e.type] || e.type}</span>
                  <span className="font-mono text-xs text-slate-500">{e.caseId}</span>
                </div>
                {e.stageId && (
                  <div className="text-xs text-slate-400">
                    {e.stageId}
                    {e.agent ? ` · ${e.agent}` : ''}
                  </div>
                )}
              </li>
            ))}
            {!feed.length && <p className="text-slate-500">No activity yet.</p>}
          </ul>
        </section>
      </div>

      {(standardized || scadMethodology || gap) && (
        <section className="mt-6">
          <h2 className="mb-3 text-sm uppercase tracking-widest text-slate-400">
            Output documents
          </h2>
          <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
            {standardized && (
              <MethodologyDoc
                title={standardized.title || 'Standardized Methodology'}
                sections={standardized.sections}
              />
            )}
            {scadMethodology && (
              <MethodologyDoc
                title={scadMethodology.title || 'SCAD-Specific Methodology'}
                sections={scadMethodology.sections}
              />
            )}
            {gap && <GapDoc gap={gap} />}
          </div>
        </section>
      )}
    </div>
  );
}
