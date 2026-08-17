import { Sparkles } from 'lucide-react';
import { SAMPLE_QUESTIONS } from '@/lib/constants';

export function EmptyChat({ onPick }: { onPick: (q: string) => void }) {
  return (
    <div className="mx-auto flex max-w-2xl flex-col items-center px-4 py-10 text-center">
      <span className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-tr from-sky-600 to-indigo-600 text-white shadow-md">
        <Sparkles className="h-7 w-7" />
      </span>
      <h2 className="text-xl font-semibold text-foreground">
        Ask about university policy
      </h2>
      <p className="mt-2 max-w-md text-sm text-muted-foreground">
        Get answers grounded in official Sanctuary University documents, complete
        with citations you can verify.
      </p>
      <div className="mt-6 grid w-full gap-2 sm:grid-cols-2">
        {SAMPLE_QUESTIONS.map((q) => (
          <button
            key={q}
            type="button"
            onClick={() => onPick(q)}
            className="rounded-xl border bg-card px-4 py-3 text-left text-sm text-foreground shadow-sm transition-colors hover:border-primary/40 hover:bg-muted"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}
