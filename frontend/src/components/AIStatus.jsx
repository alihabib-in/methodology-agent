import { cn } from '../lib/utils.js';

const STATUS_META = {
  listening: { icon: '●', label: 'Listening', sub: 'Understanding the discussion' },
  analyzing: { icon: '◌', label: 'Analyzing', sub: 'Identifying methodology requirements' },
  detecting_gaps: { icon: '◌', label: 'Reviewing methodology', sub: 'Checking for missing information' },
  generating_question: { icon: '✦', label: 'Preparing question', sub: 'Prioritizing the most important gap' },
  asking: { icon: '✦', label: 'Asking question', sub: 'Raising a question with the group' },
  waiting_for_user: { icon: '●', label: 'Waiting for response', sub: null },
  processing_answer: { icon: '◌', label: 'Processing answer', sub: 'Updating the methodology' },
  updating_methodology: { icon: '◌', label: 'Updating methodology', sub: 'Applying the latest input' },
  ready: { icon: '✓', label: 'Up to date', sub: null },
  offline: { icon: '●', label: 'Offline', sub: 'Live connection unavailable' },
  error: { icon: '!', label: 'Error', sub: 'Something went wrong' },
};

const BUSY_STATUSES = new Set([
  'analyzing',
  'detecting_gaps',
  'generating_question',
  'processing_answer',
  'updating_methodology',
]);

export default function AIStatus({ status }) {
  const meta = STATUS_META[status] || STATUS_META.offline;
  const busy = BUSY_STATUSES.has(status);

  return (
    <div
      className={cn(
        'flex items-center gap-2.5 rounded-lg bg-secondary px-3 py-2',
        status === 'ready' && 'text-emerald-700',
        status === 'error' && 'text-destructive'
      )}
    >
      <span className={cn('text-base leading-none', busy && 'ai-busy')}>{meta.icon}</span>
      <div className="flex flex-col">
        <span className="text-sm font-semibold">{meta.label}</span>
        {meta.sub && <span className="text-xs text-muted-foreground">{meta.sub}</span>}
      </div>
    </div>
  );
}
