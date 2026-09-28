import { useState } from 'react';
import { Check, X } from 'lucide-react';
import { Button } from './ui/button.jsx';
import { Input } from './ui/input.jsx';

// question domain/target_gap -> input kind. Everything else falls back to text.
const INPUT_TYPES = {
  reference_period: 'date',
  reference_date: 'date',
  frequency: 'choice',
  statistical_unit: 'choice',
  geographic_scope: 'choice',
  budget: 'number',
};

const CHOICES = {
  frequency: ['monthly', 'quarterly', 'annual', 'weekly', 'daily'],
  statistical_unit: ['establishment', 'company', 'branch', 'product', 'person'],
  geographic_scope: ['Abu Dhabi', 'National', 'Regional', 'Multiple regions'],
};

function getInputType(question) {
  const domain = question?.domain || question?.target_gap || '';
  return INPUT_TYPES[domain] || 'text';
}

export default function QuestionEditor({ question, onSave, onCancel }) {
  const type = getInputType(question);
  const [value, setValue] = useState('');
  const [error, setError] = useState(null);

  function handleSave() {
    const v = (value ?? '').trim();
    if (!v) {
      setError(type === 'choice' ? 'Please select an option.' : 'Please provide an answer.');
      return;
    }
    if (type === 'number' && Number.isNaN(Number(v))) {
      setError('Please enter a valid number.');
      return;
    }
    setError(null);
    onSave?.({ question, answer: v, type });
  }

  return (
    <div className="space-y-3">
      <p className="text-sm font-medium">{question?.question}</p>

      <label className="block">
        <span className="mb-1 block text-xs font-medium text-muted-foreground">
          {type === 'text'
            ? 'Your answer'
            : type === 'choice'
              ? 'Select an option'
              : type === 'number'
                ? 'Enter a number'
                : 'Pick a date'}
        </span>

        {type === 'text' && (
          <textarea
            className="min-h-[80px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder="Type your answer…"
          />
        )}

        {type === 'choice' && (
          <div className="space-y-2" role="radiogroup" aria-label="Options">
            {(CHOICES[question?.domain] || []).map((opt) => (
              <label key={opt} className="flex items-center gap-2 text-sm">
                <input
                  type="radio"
                  name={`q-${question?.question_id || question?.domain || 'generic'}`}
                  value={opt}
                  checked={value === opt}
                  onChange={() => setValue(opt)}
                  className="h-4 w-4 accent-[hsl(var(--primary))]"
                />
                {opt}
              </label>
            ))}
          </div>
        )}

        {type === 'number' && (
          <Input
            type="number"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder="e.g. 500000"
          />
        )}

        {type === 'date' && (
          <Input type="date" value={value} onChange={(e) => setValue(e.target.value)} />
        )}
      </label>

      {error && (
        <p className="text-xs text-destructive" role="alert">
          {error}
        </p>
      )}

      <div className="flex justify-end gap-2">
        <Button variant="ghost" size="sm" onClick={onCancel}>
          <X className="h-4 w-4" /> Cancel
        </Button>
        <Button size="sm" onClick={handleSave}>
          <Check className="h-4 w-4" /> Save
        </Button>
      </div>
    </div>
  );
}
