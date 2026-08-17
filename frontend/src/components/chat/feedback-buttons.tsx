'use client';

import { useState } from 'react';
import { ThumbsDown, ThumbsUp } from 'lucide-react';
import { useSubmitFeedback } from '@/hooks/use-feedback';
import { useToast } from '@/hooks/use-toast';
import { cn, extractError } from '@/lib/utils';

interface FeedbackButtonsProps {
  messageId: string;
  conversationId?: string | null;
}

export function FeedbackButtons({
  messageId,
  conversationId,
}: FeedbackButtonsProps) {
  const [rating, setRating] = useState<1 | -1 | null>(null);
  const submit = useSubmitFeedback(conversationId);
  const { success, error } = useToast();

  const send = (value: 1 | -1) => {
    const previous = rating;
    setRating(value);
    submit.mutate(
      { message_id: messageId, rating: value },
      {
        onSuccess: () => success('Thanks for the feedback'),
        onError: (e) => {
          setRating(previous);
          error('Could not save feedback', extractError(e));
        },
      },
    );
  };

  return (
    <div className="flex items-center gap-1">
      <button
        type="button"
        onClick={() => send(1)}
        disabled={submit.isPending}
        aria-label="Helpful"
        className={cn(
          'inline-flex h-7 w-7 items-center justify-center rounded-md transition-colors hover:bg-muted disabled:opacity-50',
          rating === 1
            ? 'text-emerald-600 dark:text-emerald-400'
            : 'text-muted-foreground',
        )}
      >
        <ThumbsUp className="h-4 w-4" />
      </button>
      <button
        type="button"
        onClick={() => send(-1)}
        disabled={submit.isPending}
        aria-label="Not helpful"
        className={cn(
          'inline-flex h-7 w-7 items-center justify-center rounded-md transition-colors hover:bg-muted disabled:opacity-50',
          rating === -1
            ? 'text-rose-600 dark:text-rose-400'
            : 'text-muted-foreground',
        )}
      >
        <ThumbsDown className="h-4 w-4" />
      </button>
    </div>
  );
}
