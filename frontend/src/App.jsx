import { useEffect, useRef, useState } from 'react';
import { Activity, BookOpen, HelpCircle, Layers, Link2, LogOut, Pencil, Sparkles } from 'lucide-react';
import JitsiMeeting from './components/JitsiMeeting.jsx';
import MethodologyAssistant from './components/MethodologyAssistant.jsx';
import AIActivityBar from './components/AIActivityBar.jsx';
import QuestionOverlay from './components/QuestionOverlay.jsx';
import QuestionEditor from './components/QuestionEditor.jsx';
import KnowledgeGraph from './components/KnowledgeGraph.jsx';
import { useRealtime } from './hooks/useRealtime.js';
import { AI_STATUS, store, useStore } from './store/store.js';
import { Button } from './components/ui/button.jsx';
import { Input } from './components/ui/input.jsx';
import { Badge } from './components/ui/badge.jsx';
import { Tabs, TabsList, TabsTrigger } from './components/ui/tabs.jsx';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from './components/ui/dialog.jsx';
import { cn } from './lib/utils.js';
import { speak } from './lib/speech.js';
import {
  analyzeSession,
  answerSession,
  createKnowledgeCandidate,
  createMeeting,
  createSession,
  deleteKnowledge,
  getSessionState,
  listKnowledge,
  logEvent,
} from './api.js';

const TABS = [
  { id: 'questions', label: 'Questions', icon: HelpCircle },
  { id: 'activity', label: 'Activity', icon: Activity },
  { id: 'state', label: 'Methodology', icon: Layers },
  { id: 'knowledge', label: 'Knowledge', icon: BookOpen },
];

const DEMO_MEETINGS = [
  {
    code: 'c968f789',
    name: 'Impact of Social Media on Youth',
    room: 'scad-m-000021-c968f789',
    session: 'M-000021',
  },
];

function getRoomFromUrl() {
  try {
    return new URLSearchParams(window.location.search).get('room') || '';
  } catch {
    return '';
  }
}

function getSessionFromUrl() {
  try {
    return new URLSearchParams(window.location.search).get('session') || '';
  } catch {
    return '';
  }
}

function shortRoomCode(roomName) {
  if (!roomName) return '';
  const parts = String(roomName).split('-');
  return parts[parts.length - 1] || roomName;
}

export default function App() {
  const [user, setUser] = useState(null);
  const [phase, setPhase] = useState('login');
  const [objective, setObjective] = useState('');
  const [sessionId, setSessionId] = useState('');
  const [joinRoom, setJoinRoom] = useState('');
  const [meeting, setMeeting] = useState(null);
  const [events, setEvents] = useState([]);
  const [knowledge, setKnowledge] = useState([]);
  const [activeTab, setActiveTab] = useState('questions');
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const [participantCount, setParticipantCount] = useState(0);
  const [copied, setCopied] = useState(false);
  const [invitedRoom] = useState(getRoomFromUrl);
  const [invitedSession] = useState(getSessionFromUrl);
  const [activeQuestion, setActiveQuestion] = useState(null);
  const [askedQuestions, setAskedQuestions] = useState(() => new Set());
  const [meetingEnded, setMeetingEnded] = useState(false);
  const [assistantOpen, setAssistantOpen] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState(null);
  const [meetingMode, setMeetingMode] = useState('new');
  const [selectedMeeting, setSelectedMeeting] = useState('');

  const jitsiRef = useRef(null);
  const remoteParticipantsRef = useRef(new Set());
  const analysisTriggeredRef = useRef(false);
  const overlayTimerRef = useRef(null);

  const aiStatus = useStore((s) => s.aiStatus);
  const gaps = useStore((s) => s.gaps);
  const questions = useStore((s) => s.questions);
  const storeObjective = useStore((s) => s.objective);
  const methodologyState = useStore((s) => s.methodologyState);
  const activity = useStore((s) => s.activity);
  const connection = useStore((s) => s.connection);

  useRealtime(sessionId);

  useEffect(() => {
    return () => {
      if (overlayTimerRef.current) clearTimeout(overlayTimerRef.current);
    };
  }, []);

  useEffect(() => {
    if (!sessionId) return undefined;
    let cancelled = false;
    getSessionState(sessionId)
      .then((data) => {
        if (cancelled) return;
        store.dispatch({
          event_type: 'state.snapshot',
          session_id: sessionId,
          payload: {
            methodology_state: data.methodology_state,
            gaps: data.gaps,
            questions: data.questions,
            recommended_question: data.recommended_question,
          },
        });
      })
      .catch(() => {});
    listKnowledge()
      .then((items) => {
        if (!cancelled) setKnowledge(items);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [sessionId]);

  function addEvent(type, payload = {}) {
    const entry = { type, payload, ts: new Date().toISOString() };
    setEvents((prev) => [...prev, entry]);
    if (meeting && meeting.meeting_id) {
      logEvent(meeting.meeting_id, type, payload, sessionId).catch(() => {});
    }
  }

  function handleLogin(name) {
    if (!name.trim()) return;
    setUser(name.trim());
    if (invitedRoom) {
      joinRoomByName(invitedRoom, invitedSession || null);
    } else {
      setPhase('setup');
    }
  }

  function handleLogout() {
    setUser(null);
    setPhase('login');
    setMeeting(null);
    setEvents([]);
    setKnowledge([]);
    setSessionId('');
    setParticipantCount(0);
    setActiveQuestion(null);
    setAskedQuestions(new Set());
    setMeetingEnded(false);
    setAssistantOpen(false);
    remoteParticipantsRef.current = new Set();
    analysisTriggeredRef.current = false;
    if (overlayTimerRef.current) clearTimeout(overlayTimerRef.current);
    store.reset();
  }

  async function handleCreateSession() {
    setError(null);
    setBusy(true);
    remoteParticipantsRef.current = new Set();
    analysisTriggeredRef.current = false;
    setParticipantCount(0);
    setKnowledge([]);
    setActiveQuestion(null);
    setAskedQuestions(new Set());
    setMeetingEnded(false);
    store.reset();
    try {
      const session = await createSession();
      const sid = session.meeting_id;
      setSessionId(sid);

      const created = await createMeeting(sid, objective.trim() || 'Methodology Session', user, user);
      setMeeting(created);
      addEvent('meeting.ready', { room: created.jitsi_room_name });

      setPhase('meeting');
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function loadAssistantContext() {
    if (!sessionId) return;
    store.setStatus(AI_STATUS.ANALYZING);
    try {
      const result = await analyzeSession(sessionId, objective || 'Methodology session');
      store.applyAnalysis(result);
    } catch (e) {
      store.setStatus(AI_STATUS.ERROR);
      setError(String(e));
    }
    listKnowledge()
      .then(setKnowledge)
      .catch(() => {});
  }

  function handleJitsiEvent(type, data) {
    addEvent(type, data || {});
  }

  function handleParticipantJoined(p) {
    if (p && p.local) return;
    if (p?.displayName && p.displayName === user) return;
    const key = p?.id || p?.displayName || 'unknown';
    remoteParticipantsRef.current.add(key);
    const count = 1 + remoteParticipantsRef.current.size;
    setParticipantCount(count);
    handleJitsiEvent('participant.joined', { id: p?.id });
    if (count >= 2 && !analysisTriggeredRef.current) {
      analysisTriggeredRef.current = true;
      loadAssistantContext();
    }
  }

  function handleParticipantLeft(p) {
    const key = p?.id || p?.displayName || 'unknown';
    remoteParticipantsRef.current.delete(key);
    setParticipantCount(1 + remoteParticipantsRef.current.size);
    handleJitsiEvent('participant.left', { id: p?.id });
  }

  function handleJoinMeeting() {
    joinRoomByName(joinRoom, null);
  }

  function handleExistingSelect(value) {
    setSelectedMeeting(value);
    if (!value) return;
    const meeting = DEMO_MEETINGS.find((m) => m.code === value);
    if (meeting) joinRoomByName(meeting.room, meeting.session);
  }

  function joinRoomByName(room, session) {
    const name = (room || '').trim();
    if (!name) return;
    setMeeting({
      meeting_id: null,
      session_id: session || null,
      jitsi_room_name: name,
      jitsi_url: '',
      token: null,
      status: 'ready',
    });
    setSessionId(session || '');
    setKnowledge([]);
    setEvents([]);
    setActiveQuestion(null);
    setAskedQuestions(new Set());
    setMeetingEnded(false);
    setParticipantCount(0);
    remoteParticipantsRef.current = new Set();
    analysisTriggeredRef.current = false;
    store.reset();
    setPhase('meeting');
  }

  function buildShareLink() {
    if (!meeting?.jitsi_room_name) return '';
    const room = encodeURIComponent(meeting.jitsi_room_name);
    let host = window.location.host;
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      const jitsiHost = (import.meta.env.VITE_JITSI_DOMAIN || '').split(':')[0];
      if (jitsiHost) {
        host = `${jitsiHost}:${window.location.port || '5173'}`;
      }
    }
    const params = [`room=${room}`];
    if (sessionId) params.push(`session=${encodeURIComponent(sessionId)}`);
    return `${window.location.protocol}//${host}/?${params.join('&')}`;
  }

  async function handleCopyLink() {
    const link = buildShareLink();
    if (!link) return;
    try {
      await navigator.clipboard.writeText(link);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      window.prompt('Copy the meeting link:', link);
    }
  }

  function handleAsk(q) {
    if (!q || !q.question) return;
    setActiveQuestion(q);
    setAskedQuestions((prev) => new Set(prev).add(q.question));
    jitsiRef.current?.sendChatMessage(q.question);
    addEvent('question.asked', { question: q.question, domain: q.domain });
    store.setStatus(AI_STATUS.ASKING);
    speak(q.question);
    if (overlayTimerRef.current) clearTimeout(overlayTimerRef.current);
    overlayTimerRef.current = setTimeout(() => {
      setActiveQuestion(null);
      store.setStatus(AI_STATUS.WAITING_FOR_USER);
    }, 15000);
  }

  function handleEndMeeting() {
    addEvent('meeting.ended', {});
    setMeetingEnded(true);
  }

  async function handleSaveAnswer(question, answer) {
    addEvent('answer.received', { question: question?.question, answer });
    setEditingQuestion(null);
    if (!sessionId) return;
    try {
      await answerSession(sessionId, answer);
      const data = await getSessionState(sessionId);
      store.dispatch({
        event_type: 'state.snapshot',
        session_id: sessionId,
        payload: {
          methodology_state: data.methodology_state,
          gaps: data.gaps,
          questions: data.questions,
          recommended_question: data.recommended_question,
        },
      });
    } catch (e) {
      setError(String(e));
    }
  }

  async function handleAddKnowledgeNode({ concept, statement, parentId }) {
    addEvent('knowledge.candidate', { concept, statement, parentId });
    try {
      await createKnowledgeCandidate(concept, statement, 'definition', parentId);
      listKnowledge().then(setKnowledge).catch(() => {});
    } catch (e) {
      setError(String(e));
    }
  }

  async function handleDeleteKnowledgeNode({ id }) {
    addEvent('knowledge.deleted', { id });
    try {
      await deleteKnowledge(id);
      listKnowledge().then(setKnowledge).catch(() => {});
    } catch (e) {
      setError(String(e));
    }
  }

  // ---------- render ----------

  if (phase === 'login') {
    return <LoginScreen onLogin={handleLogin} />;
  }

  if (phase === 'setup') {
    return (
      <div className="app-bg relative flex h-full flex-col overflow-hidden">
        <BackgroundShapes />
        <Header
          user={user}
          roomName={null}
          copied={copied}
          onCopyLink={handleCopyLink}
          onLogout={handleLogout}
        />
        <div className="relative z-10 flex flex-1 flex-col items-center gap-5 px-4 py-12">
          <h2 className="text-xl font-semibold">Welcome, {user}</h2>
          <p className="text-sm text-muted-foreground">Choose how you would like to proceed</p>

          <div
            className="flex rounded-full border bg-muted p-1"
            role="tablist"
            aria-label="Meeting type"
          >
            <button
              type="button"
              role="tab"
              aria-selected={meetingMode === 'new'}
              onClick={() => setMeetingMode('new')}
              className={cn(
                'rounded-full px-5 py-1.5 text-sm font-medium transition-colors',
                meetingMode === 'new'
                  ? 'bg-primary text-primary-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              )}
            >
              New Meeting
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={meetingMode === 'existing'}
              onClick={() => setMeetingMode('existing')}
              className={cn(
                'rounded-full px-5 py-1.5 text-sm font-medium transition-colors',
                meetingMode === 'existing'
                  ? 'bg-primary text-primary-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              )}
            >
              Existing Meeting
            </button>
          </div>

          {meetingMode === 'new' ? (
            <>
              <label className="flex w-full max-w-md flex-col gap-1.5 text-sm text-muted-foreground">
                Discussion name
                <Input
                  value={objective}
                  onChange={(e) => setObjective(e.target.value)}
                  placeholder="e.g. Impact of Social Media on Youth"
                  onKeyDown={(e) => e.key === 'Enter' && handleCreateSession()}
                />
              </label>
              <Button onClick={handleCreateSession} disabled={busy}>
                {busy ? 'Creating…' : 'Start Session'}
              </Button>
            </>
          ) : (
            <label className="flex w-full max-w-md flex-col gap-1.5 text-sm text-muted-foreground">
              Select a meeting
              <select
                value={selectedMeeting}
                onChange={(e) => handleExistingSelect(e.target.value)}
                className="h-10 w-full rounded-md border border-input bg-white px-3 text-sm text-foreground shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              >
                <option value="">Choose a meeting…</option>
                {DEMO_MEETINGS.map((m) => (
                  <option key={m.code} value={m.code}>
                    {m.code} - {m.name}
                  </option>
                ))}
              </select>
            </label>
          )}

          {error && <p className="text-sm text-destructive">{error}</p>}
        </div>
      </div>
    );
  }

  const objectiveDisplay = storeObjective?.value || objective || '';

  return (
    <div className="app-bg relative flex h-full flex-col overflow-hidden">
      <BackgroundShapes />
      <Header
        user={user}
        roomName={meeting?.jitsi_room_name}
        copied={copied}
        onCopyLink={handleCopyLink}
        onLogout={handleLogout}
        center={
          <AIActivityBar
            connection={connection}
            meetingEnded={meetingEnded}
            participantCount={participantCount}
            activity={activity}
            questionCount={questions.length}
            aiStatus={aiStatus}
          />
        }
      />

      {connection === 'reconnecting' && (
        <div className="relative z-10 bg-amber-50 px-4 py-1 text-center text-sm text-amber-700">
          ● Live connection lost — Reconnecting…
        </div>
      )}

      <div className="meeting-fade relative z-10 flex min-h-0 flex-1 gap-3 p-3">
        <div className="relative min-w-0 flex-1 overflow-hidden rounded-xl border bg-black shadow-sm">
          {meetingEnded ? (
            <div className="flex h-full items-center justify-center text-lg font-medium text-neutral-400">
              Meeting Room Empty
            </div>
          ) : (
            <>
              <JitsiMeeting
                ref={jitsiRef}
                roomName={meeting.jitsi_room_name}
                jwt={meeting.token}
                displayName={user}
                onReady={() => addEvent('meeting.joined', {})}
                onParticipantJoined={handleParticipantJoined}
                onParticipantLeft={handleParticipantLeft}
                onMeetingEnded={handleEndMeeting}
              />
              <QuestionOverlay status={aiStatus} question={activeQuestion} />
            </>
          )}
        </div>

        <div className="flex w-[500px] shrink-0 flex-col overflow-hidden rounded-xl border bg-white shadow-sm">
          <Tabs
            value={activeTab}
            onValueChange={setActiveTab}
            className="flex min-h-0 flex-1 flex-col"
          >
            <TabsList className="mx-2 mt-2 flex h-9 shrink-0 items-center justify-between gap-1">
              {TABS.map((tab) => {
                const Icon = tab.icon;
                return (
                  <TabsTrigger key={tab.id} value={tab.id} className="flex items-center gap-1.5">
                    <Icon className="h-4 w-4" />
                    {tab.label}
                  </TabsTrigger>
                );
              })}
            </TabsList>
            <div className="flex min-h-0 flex-1 flex-col p-4">
              {activeTab === 'questions' && (
                <div className="min-h-0 flex-1 overflow-y-auto">
                  <QuestionsPanel
                    questions={questions}
                    askedQuestions={askedQuestions}
                    onAsk={handleAsk}
                    onEdit={setEditingQuestion}
                  />
                </div>
              )}
              {activeTab === 'activity' && (
                <div className="min-h-0 flex-1 overflow-y-auto">
                  <ActivityPanel events={events} />
                </div>
              )}
              {activeTab === 'state' && (
                <div className="min-h-0 flex-1 overflow-y-auto">
                  <StatePanel state={methodologyState} />
                </div>
              )}
              {activeTab === 'knowledge' && (
                <KnowledgeGraph
                  methodologyName={methodologyState?.objective?.value}
                  nodes={knowledge}
                  onAddNode={handleAddKnowledgeNode}
                  onDeleteNode={handleDeleteKnowledgeNode}
                />
              )}
            </div>
          </Tabs>
        </div>
      </div>

      <button
        className="assistant-fab"
        onClick={() => setAssistantOpen(true)}
        aria-label="Open AI Methodology Assistant"
        title="AI Methodology Assistant"
      >
        <Sparkles className="h-6 w-6" />
      </button>

      <Dialog open={assistantOpen} onOpenChange={setAssistantOpen}>
        <DialogContent className="max-h-[85vh] max-w-xl overflow-y-auto">
          <DialogHeader>
            <DialogTitle>AI Methodology Assistant</DialogTitle>
            <DialogDescription>Live methodology insights for this session</DialogDescription>
          </DialogHeader>
          <MethodologyAssistant
            objective={objectiveDisplay}
            gaps={gaps}
            state={methodologyState}
            participantCount={participantCount}
            aiStatus={aiStatus}
          />
        </DialogContent>
      </Dialog>

      <Dialog open={!!editingQuestion} onOpenChange={(open) => !open && setEditingQuestion(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Edit Answer</DialogTitle>
            <DialogDescription>Provide an answer for this question.</DialogDescription>
          </DialogHeader>
          {editingQuestion && (
            <QuestionEditor
              question={editingQuestion}
              onSave={(r) => handleSaveAnswer(r.question, r.answer)}
              onCancel={() => setEditingQuestion(null)}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

function BackgroundShapes() {
  return (
    <>
      <div className="login-shape login-shape-1" aria-hidden="true" />
      <div className="login-shape login-shape-2" aria-hidden="true" />
      <div className="login-shape login-shape-3" aria-hidden="true" />
    </>
  );
}

function Header({ user, roomName, copied, onCopyLink, onLogout, center }) {
  return (
    <header className="relative z-10 grid grid-cols-[1fr_auto_1fr] items-center gap-3 border-b bg-white/90 px-4 py-2 backdrop-blur">
      <div className="justify-self-start">
        <img src="/logo.png" alt="AI Methodology Discussions" className="h-12 w-auto" />
      </div>
      <div className="justify-self-center">{center}</div>
      <div className="flex items-center justify-self-end gap-3">
        {roomName && (
          <Button
            variant="outline"
            size="sm"
            onClick={onCopyLink}
            title={`Copy link for room ${roomName}`}
            aria-label={`Copy link for room ${roomName}`}
          >
            <Link2 className="h-4 w-4" />
            {copied ? 'Copied!' : shortRoomCode(roomName)}
          </Button>
        )}
        <span className="text-sm text-muted-foreground">{user}</span>
        <Button
          variant="ghost"
          size="icon"
          onClick={onLogout}
          aria-label="Logout"
          title="Logout"
        >
          <LogOut className="h-4 w-4" />
        </Button>
      </div>
    </header>
  );
}

function LoginScreen({ onLogin }) {
  const [name, setName] = useState('');
  return (
    <div className="login-bg relative flex h-full flex-col items-center justify-center gap-6 overflow-hidden">
      <div className="login-shape login-shape-1" aria-hidden="true" />
      <div className="login-shape login-shape-2" aria-hidden="true" />
      <div className="login-shape login-shape-3" aria-hidden="true" />
      <div className="relative z-10 flex flex-col items-center gap-6">
        <img src="/logo.png" alt="Logo" className="h-20 w-auto" />
        <h1 className="text-2xl font-semibold tracking-tight">
          AI Methodology Discussions
        </h1>
        <Input
          className="w-72 text-center"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Enter your name"
          onKeyDown={(e) => e.key === 'Enter' && onLogin(name)}
        />
        <Button className="w-72" onClick={() => onLogin(name)}>
          Login
        </Button>
      </div>
    </div>
  );
}

function QuestionsPanel({ questions, askedQuestions, onAsk, onEdit }) {
  if (!questions.length) return <p className="text-sm text-muted-foreground">No questions yet.</p>;
  return (
    <ul className="space-y-2">
      {questions.map((q, i) => {
        const asked = askedQuestions.has(q.question);
        return (
          <li key={i} className="flex items-start gap-3 rounded-md bg-muted p-2">
            <span className="min-w-6 font-semibold text-primary">{i + 1}.</span>
            <span className="flex-1 text-sm">{q.question}</span>
            <Button size="sm" variant="secondary" onClick={() => onAsk(q)} disabled={asked}>
              {asked ? 'Asked' : 'Ask'}
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => onEdit(q)}
              aria-label="Edit answer"
              title="Edit answer"
            >
              <Pencil className="h-3.5 w-3.5" />
            </Button>
          </li>
        );
      })}
    </ul>
  );
}

function ActivityPanel({ events }) {
  if (!events.length) return <p className="text-sm text-muted-foreground">No activity yet.</p>;
  const sorted = [...events].sort((a, b) => new Date(a.ts) - new Date(b.ts));
  return (
    <ul className="space-y-1">
      {sorted.map((e, i) => (
        <li key={i} className="flex items-start gap-3">
          <span className="w-20 shrink-0 text-xs tabular-nums text-muted-foreground">
            {formatTime(e.ts)}
          </span>
          <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-primary" />
          <div className="flex flex-col">
            <span className="text-sm font-medium">{e.type}</span>
            {e.payload?.question && (
              <span className="text-xs text-muted-foreground">“{e.payload.question}”</span>
            )}
            {e.payload?.id && <span className="text-xs text-muted-foreground">{e.payload.id}</span>}
            {e.payload?.room && <span className="text-xs text-muted-foreground">{e.payload.room}</span>}
          </div>
        </li>
      ))}
    </ul>
  );
}

const FIELD_LABELS = {
  objective: 'Objective',
  scope: 'Scope',
  target_population: 'Target population',
  statistical_unit: 'Statistical unit',
  reference_period: 'Reference period',
  frequency: 'Frequency',
  geographic_scope: 'Geographic scope',
  budget: 'Budget',
};

const STATUS_VARIANT = {
  confirmed: 'success',
  inferred: 'secondary',
  proposed: 'warning',
  unknown: 'outline',
  conflicting: 'destructive',
  rejected: 'destructive',
};

function FieldRow({ label, field }) {
  if (!field) return null;
  const hasValue = field.value != null && field.value !== '';
  return (
    <li className="flex flex-col gap-1 rounded-md bg-muted p-2.5">
      <span className="text-[11px] uppercase tracking-wide text-muted-foreground">{label}</span>
      <span className="text-sm">{hasValue ? field.value : '—'}</span>
      <Badge variant={STATUS_VARIANT[field.status] || 'outline'} className="w-fit">
        {field.status || 'unknown'}
      </Badge>
    </li>
  );
}

function ListSection({ title, items, getLabel }) {
  if (!items || !items.length) return null;
  return (
    <div className="space-y-1">
      <h4 className="text-xs font-semibold uppercase tracking-wide text-primary">{title}</h4>
      <ul className="space-y-1">
        {items.map((item, i) => (
          <li
            key={i}
            className="flex items-center justify-between gap-2 border-l-2 border-border py-1 pl-2 text-sm"
          >
            <span>
              {getLabel
                ? getLabel(item)
                : item.value || item.statement || item.concept || item.note || item.name || '—'}
            </span>
            {item.status && (
              <Badge variant={STATUS_VARIANT[item.status] || 'outline'} className="shrink-0">
                {item.status}
              </Badge>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

function StatePanel({ state }) {
  if (!state) return <p className="text-sm text-muted-foreground">No methodology state yet.</p>;

  const fields = [
    ['objective', FIELD_LABELS.objective],
    ['scope', FIELD_LABELS.scope],
    ['target_population', FIELD_LABELS.target_population],
    ['statistical_unit', FIELD_LABELS.statistical_unit],
    ['reference_period', FIELD_LABELS.reference_period],
    ['frequency', FIELD_LABELS.frequency],
    ['geographic_scope', FIELD_LABELS.geographic_scope],
    ['budget', FIELD_LABELS.budget],
  ];

  const hasCore = fields.some(([key]) => {
    const f = state[key];
    return f && (f.value || f.status !== 'unknown' || f.confidence);
  });

  const isEmpty =
    !hasCore &&
    !state.indicators?.length &&
    !state.dimensions?.length &&
    !state.data_sources?.length &&
    !state.definitions?.length &&
    !state.decisions?.length &&
    !state.open_questions?.length &&
    !state.constraints?.length &&
    !state.roles?.length &&
    !state.success_metrics?.length &&
    !state.training_needs?.length;

  return (
    <div className="space-y-4">
      {hasCore && (
        <div className="space-y-2">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-primary">
            Methodology
          </h3>
          <ul className="grid gap-2 sm:grid-cols-2">
            {fields.map(([key, label]) => (
              <FieldRow key={key} label={label} field={state[key]} />
            ))}
          </ul>
        </div>
      )}

      <ListSection title="Indicators" items={state.indicators} />
      <ListSection title="Dimensions" items={state.dimensions} />
      <ListSection title="Data sources" items={state.data_sources} getLabel={(d) => d.name || d.concept} />
      <ListSection title="Definitions" items={state.definitions} getLabel={(d) => d.statement || d.concept} />
      <ListSection title="Decisions" items={state.decisions} getLabel={(d) => d.value || d.concept} />
      <ListSection title="Constraints" items={state.constraints} getLabel={(d) => d.value || d.concept} />
      <ListSection title="Roles" items={state.roles} getLabel={(d) => d.role || d.value || d.concept} />
      <ListSection title="Success metrics" items={state.success_metrics} getLabel={(d) => d.metric || d.value || d.concept} />
      <ListSection title="Training needs" items={state.training_needs} getLabel={(d) => d.need || d.value || d.concept} />
      <ListSection title="Open questions" items={state.open_questions} getLabel={(d) => d.note || d.concept} />

      {isEmpty && <p className="text-sm text-muted-foreground">No methodology content yet.</p>}
    </div>
  );
}

function KnowledgePanel({ items }) {
  if (!items.length) return <p className="text-sm text-muted-foreground">No knowledge captured yet.</p>;
  return (
    <ul className="space-y-2">
      {items.map((k) => (
        <li key={k.knowledge_id} className="rounded-md bg-muted p-3">
          <div className="flex items-center justify-between gap-2">
            <strong className="text-sm text-primary">{k.concept}</strong>
            <Badge variant={STATUS_VARIANT[k.status] || 'secondary'}>{k.status}</Badge>
          </div>
          {k.statement && <p className="mt-1 text-sm">{k.statement}</p>}
          {k.domain && <span className="mt-1 block text-xs text-muted-foreground">Domain: {k.domain}</span>}
        </li>
      ))}
    </ul>
  );
}

function formatTime(ts) {
  try {
    return new Date(ts).toLocaleTimeString();
  } catch {
    return ts;
  }
}
