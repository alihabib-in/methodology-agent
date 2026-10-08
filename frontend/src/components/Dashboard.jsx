import { useEffect, useState } from 'react';

const STAGES = [
  { id: 'requirement_case', label: 'Requirement Case', icon: '🎯' },
  { id: 'case_analysis', label: 'Case Analysis', icon: '🧠' },
  { id: 'data_acquisition', label: 'Data Acquisition', icon: '📊' },
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
  'data_acquisition',
  'international_research',
  'standardized_methodology',
  'scad_methodology',
  'indicator_development',
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

const DEFAULT_INPUT = `We need to develop a methodology for the AI Adoption Index in Abu Dhabi, based on the 2025 AI survey. The index should cover government entities, large private companies, SMEs, and startups. Data will come from the survey, telecom providers, and cloud providers. We need to define the sampling frame, KPIs, weighting scheme, sector classification, and data privacy rules. The definition of "AI adoption" is not yet agreed and needs confirmation.`;

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

function IndicatorsDoc({ indicators }) {
  if (!indicators?.length) return null;
  return (
    <div className="dash-fade-in rounded-xl border border-slate-800 bg-slate-900 p-5">
      <h3 className="mb-3 text-lg font-semibold text-slate-100">Indicator Cards</h3>
      <div className="space-y-3">
        {indicators.map((ind) => (
          <div key={ind.code || ind.name} className="rounded-lg bg-slate-800/50 p-3">
            <div className="font-semibold text-blue-300">
              {ind.code ? `${ind.code} — ` : ''}{ind.name}
            </div>
            {ind.description && (
              <p className="mt-1 text-sm text-slate-300">{ind.description}</p>
            )}
            <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-400">
              {ind.measurement_unit && <span>Unit: {ind.measurement_unit}</span>}
              {ind.publication_frequency && <span>Frequency: {ind.publication_frequency}</span>}
              {ind.theme && <span>Theme: {ind.theme}</span>}
              {ind.reference_period && <span>Ref. period: {ind.reference_period}</span>}
            </div>
            {ind.statistical_population && (
              <p className="mt-1 text-xs text-slate-400">{ind.statistical_population}</p>
            )}
            {Array.isArray(ind.data_sources) && ind.data_sources.length > 0 && (
              <p className="mt-1 text-xs text-slate-400">
                Sources: {ind.data_sources.join(', ')}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function DataSourcesDoc({ dataAcquisition }) {
  const datasets =
    dataAcquisition?.datasets || dataAcquisition?.evidence_package?.datasets || [];
  const queries = dataAcquisition?.evidence_package?.queries || [];
  if (!datasets.length) return null;
  return (
    <div className="dash-fade-in rounded-xl border border-slate-800 bg-slate-900 p-5">
      <h3 className="mb-3 text-lg font-semibold text-slate-100">Data sources (retrieved)</h3>
      {queries.length > 0 && (
        <p className="mb-3 text-xs text-slate-500">
          Search queries: {queries.join(', ')}
        </p>
      )}
      <div className="space-y-2">
        {datasets.map((d) => (
          <div key={`${d.portal}-${d.dataset_id}`} className="rounded-lg bg-slate-800/50 p-3">
            <div className="flex items-center justify-between gap-2">
              <span className="font-mono text-xs uppercase text-blue-300">{d.portal}</span>
              <span className="font-mono text-xs text-slate-500">{d.dataset_id}</span>
            </div>
            <div className="font-medium text-slate-200">{d.title}</div>
            {d.portal === 'worldbank' && Array.isArray(d.latest) && d.latest.length > 0 && (
              <div className="mt-1 text-xs text-slate-400">
                {d.latest
                  .slice(0, 3)
                  .map((v) => `${v.year}: ${v.value}`)
                  .join(' · ')}
              </div>
            )}
            {d.portal === 'eurostat' && d.data_points != null && (
              <div className="mt-1 text-xs text-slate-400">
                {d.data_points} data points
                {Array.isArray(d.dimensions) && d.dimensions.length > 0
                  ? ` · ${d.dimensions.join(', ')}`
                  : ''}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [connected, setConnected] = useState('connecting');
  const [cases, setCases] = useState({});
  const [feed, setFeed] = useState([]);
  const [documents, setDocuments] = useState({});
  const [busy, setBusy] = useState(false);
  const [inputText, setInputText] = useState(DEFAULT_INPUT);
  const [creating, setCreating] = useState(false);
  const [createStatus, setCreateStatus] = useState('');
  const [createError, setCreateError] = useState('');

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

  async function createCase() {
    const text = inputText.trim();
    if (!text) {
      setCreateError('Please enter a methodology case description first.');
      return;
    }
    if (creating) return;
    setCreating(true);
    setCreateError('');
    setCreateStatus('Creating meeting case…');
    try {
      const res = await api('/cases', {
        method: 'POST',
        body: JSON.stringify({ text, language: 'en', title: 'New Methodology Case', force: true }),
      });
      const data = await res.json();
      const caseId = data?.case?.case_id;
      if (!caseId) {
        const detail = data?.detail;
        throw new Error(detail?.reason || (detail && JSON.stringify(detail)) || 'no case id returned');
      }

      setCases((prev) => ({
        ...prev,
        [caseId]: {
          title: data.case.title,
          objective: data.case.objective,
          status: data.case.status,
          stages: { requirement_case: { status: 'WAITING_FOR_HUMAN' } },
          updatedAt: Date.now(),
        },
      }));

      setCreateStatus('Confirming case…');
      await api(`/cases/${caseId}/confirm`, {
        method: 'POST',
        body: JSON.stringify({ decision: 'confirm' }),
      });
      setCreateStatus('Running agents…');
      await api(`/cases/${caseId}/advance`, { method: 'POST', body: JSON.stringify({}) });
      setCreateStatus('');
    } catch (err) {
      console.error('createCase failed', err);
      setCreateError(String(err?.message || err));
    } finally {
      setCreating(false);
    }
  }

  async function resetCase(caseId) {
    setBusy(true);
    try {
      await api(`/cases/${caseId}/reset`, { method: 'POST', body: JSON.stringify({}) });
      const detailRes = await api(`/cases/${caseId}`);
      const detail = await detailRes.json();
      const stages = {};
      for (const [sid, status] of Object.entries(detail.workflow?.stages || {})) {
        stages[sid] = { status };
      }
      setCases((prev) => ({
        ...prev,
        [caseId]: {
          ...(prev[caseId] || {}),
          status: detail.case?.status,
          stages,
          updatedAt: Date.now(),
        },
      }));
      setDocuments((prev) => ({ ...prev, [caseId]: {} }));
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

  useEffect(() => {
    async function loadCases() {
      try {
        const res = await api('/cases');
        const list = await res.json();
        for (const c of list) {
          const detailRes = await api(`/cases/${c.case_id}`);
          if (!detailRes.ok) continue;
          const detail = await detailRes.json();
          const stages = {};
          for (const [sid, status] of Object.entries(detail.workflow?.stages || {})) {
            stages[sid] = { status };
          }
          for (const a of detail.audit || []) {
            const p = a.payload || {};
            if (!p.stage) continue;
            const st = stages[p.stage] || (stages[p.stage] = {});
            if (Array.isArray(p.reasoning) && p.reasoning.length) st.reasoning = p.reasoning;
            if (p.agent) st.agent = p.agent;
            if (p.output_keys) st.output_keys = p.output_keys;
          }
          setCases((prev) => ({
            ...prev,
            [c.case_id]: {
              ...(prev[c.case_id] || {}),
              title: c.title,
              objective: c.objective,
              status: c.status,
              stages: { ...(prev[c.case_id]?.stages || {}), ...stages },
              updatedAt:
                prev[c.case_id]?.updatedAt || new Date(c.created_at || Date.now()).getTime(),
            },
          }));

          for (const stageId of DOC_STAGES) {
            if (stages[stageId]?.status === 'COMPLETED') {
              await fetchOutput(c.case_id, stageId);
            }
          }
        }
      } catch {
        // ignore
      }
    }
    loadCases();
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

  const dataAcquisition = activeDocs.data_acquisition;
  const standardized = activeDocs.standardized_methodology?.methodology;
  const scadMethodology = activeDocs.scad_methodology?.methodology;
  const indicators = activeDocs.indicator_development?.indicators;
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

      <section className="mb-6 rounded-xl border border-slate-800 bg-slate-900 p-5">
        <h2 className="mb-3 text-sm uppercase tracking-widest text-slate-400">
          Trigger — create a meeting case and run the agents
        </h2>
        <textarea
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          rows={3}
          className="mb-3 w-full rounded-lg border border-slate-700 bg-slate-950 p-3 font-mono text-sm text-slate-100"
        />
        <button
          onClick={createCase}
          disabled={creating}
          className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-emerald-500 disabled:opacity-50"
        >
          {creating ? 'Working…' : '▶ Create Meeting Case & Run Agents'}
        </button>
        {createStatus && (
          <p className="mt-2 text-sm text-blue-300">{createStatus}</p>
        )}
        {createError && (
          <p className="mt-2 text-sm text-red-400">{createError}</p>
        )}
      </section>

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
              {activeCaseId && (
                <button
                  onClick={() => resetCase(activeCaseId)}
                  disabled={busy}
                  className="rounded-lg bg-slate-700 px-3 py-1.5 text-sm font-medium text-slate-200 transition-colors hover:bg-slate-600 disabled:opacity-50"
                >
                  ↺ Reset
                </button>
              )}
            </div>
          </div>

          {activeCase && (
            <div className="mb-3 rounded-lg bg-slate-800/60 p-3">
              <div className="font-semibold text-slate-100">{activeCase.title || activeCaseId}</div>
              {activeCase.objective && (
                <div className="text-sm text-slate-300">{activeCase.objective}</div>
              )}
            </div>
          )}

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

      {(dataAcquisition || standardized || scadMethodology || indicators || gap) && (
        <section className="mt-6">
          <h2 className="mb-3 text-sm uppercase tracking-widest text-slate-400">
            Output documents
          </h2>
          <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
            {dataAcquisition && <DataSourcesDoc dataAcquisition={dataAcquisition} />}
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
            {indicators && <IndicatorsDoc indicators={indicators} />}
            {gap && <GapDoc gap={gap} />}
          </div>
        </section>
      )}
    </div>
  );
}
