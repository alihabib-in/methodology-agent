import { cn } from '../lib/utils.js';

const BUSY_STATUSES = new Set([
  'analyzing',
  'detecting_gaps',
  'generating_question',
  'processing_answer',
  'updating_methodology',
  'asking',
]);

function deriveState({ connection, meetingEnded, participantCount, activity, questionCount, aiStatus }) {
  if (connection && connection !== 'connected') {
    return { label: 'Offline', tone: 'idle' };
  }
  if (meetingEnded) {
    return { label: 'Meeting room empty', tone: 'idle' };
  }
  if (BUSY_STATUSES.has(aiStatus)) {
    return { label: 'AI is working…', tone: 'busy' };
  }
  if (activity && activity.length) {
    return { label: activity[0].label, tone: 'active' };
  }
  if (questionCount > 0) {
    return { label: 'Insights ready', tone: 'active' };
  }
  if (participantCount >= 2) {
    return { label: 'AI is listening', tone: 'listening' };
  }
  if (participantCount >= 1) {
    return { label: 'Waiting for participants', tone: 'waiting' };
  }
  return { label: 'Ready', tone: 'idle' };
}

function toneClass(tone) {
  switch (tone) {
    case 'active':
    case 'busy':
      return 'bg-primary ai-busy';
    case 'waiting':
      return 'bg-amber-500 ai-busy';
    case 'idle':
      return 'bg-muted-foreground/40';
    default:
      return 'bg-primary ai-busy';
  }
}

export default function AIActivityBar({
  connection,
  meetingEnded,
  participantCount,
  activity,
  questionCount,
  aiStatus,
}) {
  const state = deriveState({
    connection,
    meetingEnded,
    participantCount,
    activity,
    questionCount,
    aiStatus,
  });

  return (
    <div className="flex items-center gap-2">
      {state.tone === 'listening' ? (
        <span className="ai-listening-dots" aria-hidden="true">
          <span className="dot" />
          <span className="dot" />
          <span className="dot" />
        </span>
      ) : (
        <span className={cn('h-2 w-2 shrink-0 rounded-full', toneClass(state.tone))} aria-hidden="true" />
      )}
      <span className="text-xs font-medium text-muted-foreground">{state.label}</span>
    </div>
  );
}
