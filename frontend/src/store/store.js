import { useSyncExternalStore } from 'react';

export const AI_STATUS = {
  LISTENING: 'listening',
  ANALYZING: 'analyzing',
  DETECTING_GAPS: 'detecting_gaps',
  GENERATING_QUESTION: 'generating_question',
  ASKING: 'asking',
  WAITING_FOR_USER: 'waiting_for_user',
  PROCESSING_ANSWER: 'processing_answer',
  UPDATING_METHODOLOGY: 'updating_methodology',
  READY: 'ready',
  OFFLINE: 'offline',
  ERROR: 'error',
};

const MAX_ACTIVITY = 20;
const MAX_SEEN = 500;

function activityLabel(eventType) {
  switch (eventType) {
    case 'objective.detected':
    case 'objective.updated':
      return 'Objective updated';
    case 'gap.detected':
      return 'Gap detected';
    case 'gap.resolved':
      return 'Gap resolved';
    case 'question.generated':
      return 'Question generated';
    case 'question.asked':
      return 'Question asked';
    case 'answer.received':
      return 'Answer received';
    case 'knowledge.candidate':
      return 'Knowledge captured';
    case 'knowledge.approved':
      return 'Knowledge approved';
    case 'knowledge.published':
      return 'Knowledge published';
    case 'transcript.segment':
      return 'Transcript received';
    case 'participant.joined':
      return 'Participant joined';
    case 'participant.left':
      return 'Participant left';
    case 'methodology.updated':
      return 'Methodology updated';
    default:
      return null;
  }
}

function upsertGap(gaps, gap) {
  if (!gap) return gaps;
  const idx = gaps.findIndex((g) => g.domain === gap.domain);
  if (idx === -1) return [...gaps, gap];
  const next = gaps.slice();
  next[idx] = { ...next[idx], ...gap };
  return next;
}

function createRealtimeStore() {
  let state = {
    aiStatus: AI_STATUS.OFFLINE,
    connection: 'disconnected',
    methodologyState: null,
    objective: null,
    gaps: [],
    question: null,
    questions: [],
    questionIndex: 0,
    activity: [],
    seenEventIds: [],
  };

  const listeners = new Set();

  function getState() {
    return state;
  }

  function setState(partial) {
    const next = typeof partial === 'function' ? partial(state) : partial;
    state = { ...state, ...next };
    listeners.forEach((l) => l());
  }

  function subscribe(listener) {
    listeners.add(listener);
    return () => listeners.delete(listener);
  }

  function dispatch(event) {
    if (event.event_id && state.seenEventIds.includes(event.event_id)) {
      return;
    }

    const seenEventIds = event.event_id
      ? [...state.seenEventIds, event.event_id].slice(-MAX_SEEN)
      : state.seenEventIds;

    const updates = { seenEventIds };
    const type = event.event_type;
    const payload = event.payload || {};

    switch (type) {
      case 'ai.status.changed':
        updates.aiStatus = payload.status;
        break;
      case 'state.snapshot': {
        const questions =
          payload.questions ||
          (payload.recommended_question ? [payload.recommended_question] : []);
        updates.methodologyState = payload.methodology_state || null;
        updates.gaps = payload.gaps || [];
        updates.questions = questions;
        updates.questionIndex = 0;
        updates.question = questions[0] || payload.recommended_question || null;
        updates.objective = payload.methodology_state?.objective || null;
        if (questions.length > 0) {
          updates.aiStatus = AI_STATUS.READY;
        }
        break;
      }
      case 'methodology.updated':
        updates.methodologyState = payload.methodology_state;
        break;
      case 'objective.detected':
      case 'objective.updated':
        updates.objective = payload.objective;
        break;
      case 'gap.detected':
      case 'gap.updated':
        updates.gaps = upsertGap(state.gaps, payload.gap);
        break;
      case 'gap.resolved':
        updates.gaps = state.gaps.filter((g) => g.domain !== payload.domain);
        break;
      case 'question.generated':
      case 'question.presented':
        updates.question = payload.question;
        break;
      case 'question.asked':
        updates.question = { ...(state.question || {}), status: 'asked' };
        break;
      case 'system.error':
        updates.aiStatus = AI_STATUS.ERROR;
        break;
      default:
        break;
    }

    const label = activityLabel(type);
    if (label) {
      updates.activity = [
        { id: event.event_id, type, label, ts: event.timestamp },
        ...state.activity,
      ].slice(0, MAX_ACTIVITY);
    }

    setState(updates);
  }

  function applyAnalysis(result) {
    const stateDict = result.methodology_state || {};
    const questions = result.questions
      ? result.questions
      : result.recommended_question
        ? [result.recommended_question]
        : [];
    setState({
      methodologyState: stateDict,
      objective: stateDict.objective || null,
      gaps: result.gaps || [],
      questions,
      questionIndex: 0,
      question: questions[0] || result.recommended_question || null,
      aiStatus: AI_STATUS.READY,
    });
  }

  function setConnection(connection) {
    let aiStatus = state.aiStatus;
    if (
      connection === 'connected' &&
      (aiStatus === AI_STATUS.OFFLINE || aiStatus === AI_STATUS.ERROR)
    ) {
      aiStatus = AI_STATUS.LISTENING;
    } else if (
      (connection === 'disconnected' || connection === 'reconnecting') &&
      aiStatus !== AI_STATUS.ERROR
    ) {
      aiStatus = AI_STATUS.OFFLINE;
    }
    setState({ connection, aiStatus });
  }

  function setStatus(status) {
    setState({ aiStatus: status });
  }

  function setQuestionIndex(index) {
    const questions = state.questions || [];
    const next = Math.max(0, Math.min(index, questions.length - 1));
    setState({
      questionIndex: next,
      question: questions[next] || null,
    });
  }

  function reset() {
    state = {
      aiStatus: AI_STATUS.OFFLINE,
      connection: 'disconnected',
      methodologyState: null,
      objective: null,
      gaps: [],
      question: null,
      questions: [],
      questionIndex: 0,
      activity: [],
      seenEventIds: [],
    };
    listeners.forEach((l) => l());
  }

  return {
    getState,
    subscribe,
    dispatch,
    applyAnalysis,
    setConnection,
    setStatus,
    setQuestionIndex,
    reset,
  };
}

export const store = createRealtimeStore();

export function useStore(selector) {
  return useSyncExternalStore(
    store.subscribe,
    () => selector(store.getState()),
    () => selector(store.getState())
  );
}
