import AIStatus from './AIStatus.jsx';

export default function QuestionOverlay({ status, question }) {
  if (!question || !question.question) return null;
  return (
    <div className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center p-6">
      <div className="pointer-events-auto flex max-w-xl flex-col items-center gap-3 text-center">
        <AIStatus status={status} />
        <p className="rounded-lg bg-black/60 px-5 py-3 text-lg font-medium leading-snug text-white shadow-lg">
          “{question.question}”
        </p>
      </div>
    </div>
  );
}
