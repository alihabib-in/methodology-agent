import AIStatus from './AIStatus.jsx';

const STATUS_ICON = {
  confirmed: '✓',
  inferred: '~',
  proposed: '~',
  unknown: '?',
  conflicting: '!',
  rejected: '✕',
};

function SimpleList({ items, getText }) {
  if (!items || !items.length) return null;
  return (
    <ul className="space-y-1">
      {items.map((item, i) => (
        <li key={i} className="border-l-2 border-border pl-2 text-sm">
          {getText
            ? getText(item)
            : item.value || item.role || item.metric || item.need || item.concept}
        </li>
      ))}
    </ul>
  );
}

export default function MethodologyAssistant({
  objective,
  gaps,
  state,
  participantCount,
  aiStatus,
}) {
  const ready = participantCount >= 2;
  const hasData =
    (gaps && gaps.length > 0) ||
    !!state?.scope?.value ||
    !!state?.budget?.value ||
    (state?.indicators?.length > 0) ||
    (state?.roles?.length > 0) ||
    (state?.definitions?.length > 0);
  const showResults = ready || hasData;

  const scope = state?.scope?.value;
  const budget = state?.budget?.value;

  return (
    <div className="space-y-5">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-primary">
        AI Methodology Assistant
      </h2>
      <AIStatus status={aiStatus} />

      <section>
        <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Objective
        </h3>
        <p className="text-sm">{objective || 'No objective defined yet'}</p>
      </section>

      {!showResults ? (
        <p className="text-sm text-muted-foreground">
          Waiting for participants to join and start discussing…
        </p>
      ) : (
        <>
          {scope && (
            <section>
              <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Scope
              </h3>
              <p className="text-sm">{scope}</p>
            </section>
          )}

          {budget && (
            <section>
              <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Budget
              </h3>
              <p className="text-sm">{budget}</p>
            </section>
          )}

          {state?.constraints?.length > 0 && (
            <section>
              <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Constraints
              </h3>
              <SimpleList items={state.constraints} getText={(c) => c.value || c.concept} />
            </section>
          )}

          {state?.roles?.length > 0 && (
            <section>
              <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Roles
              </h3>
              <SimpleList items={state.roles} getText={(r) => r.role || r.value || r.concept} />
            </section>
          )}

          {state?.success_metrics?.length > 0 && (
            <section>
              <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Success Metrics
              </h3>
              <SimpleList items={state.success_metrics} getText={(m) => m.metric || m.value || m.concept} />
            </section>
          )}

          {state?.training_needs?.length > 0 && (
            <section>
              <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Training Needs
              </h3>
              <SimpleList items={state.training_needs} getText={(t) => t.need || t.value || t.concept} />
            </section>
          )}

          <section>
            <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Methodology gaps
            </h3>
            {gaps && gaps.length > 0 ? (
              <ul className="space-y-0.5">
                {gaps.map((gap) => (
                  <li key={gap.domain} className="flex gap-2 text-sm">
                    <span className="w-4 text-center text-amber-600">
                      {STATUS_ICON[gap.status] || '?'}
                    </span>
                    <span>{gap.label || gap.domain}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-muted-foreground">No gaps detected.</p>
            )}
          </section>
        </>
      )}
    </div>
  );
}
