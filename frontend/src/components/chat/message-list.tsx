'use client';

import { useEffect, useRef } from 'react';
import { Bot } from 'lucide-react';
import { Citation, Message, MessageRole } from '@/lib/types';
import { getCitations } from '@/lib/utils';
import { MessageBubble } from './message-bubble';
import { TypingIndicator } from './typing-indicator';

interface MessageListProps {
  messages: Message[];
  conversationId?: string | null;
  /** Live (not-yet-persisted) user question shown below the server history. */
  pendingQuery?: string | null;
  /** Live assistant answer being streamed; renders with a caret, no feedback. */
  streamingAnswer?: { text: string; citations: Citation[] } | null;
  /** Waiting for the first token — show the typing indicator. */
  isSending?: boolean;
  /** Gate feedback controls off for every message (e.g. the guest chat). */
  allowFeedback?: boolean;
}

export function MessageList({
  messages,
  conversationId,
  pendingQuery,
  streamingAnswer,
  isSending,
  allowFeedback = true,
}: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length, pendingQuery, streamingAnswer?.text, isSending]);

  return (
    <div className="mx-auto w-full max-w-3xl space-y-6 px-4 py-6">
      {messages.map((m) => (
        <MessageBubble
          key={m.id}
          role={m.role}
          content={m.content}
          citations={getCitations(m)}
          messageId={m.role === MessageRole.ASSISTANT ? m.id : undefined}
          conversationId={conversationId}
          allowFeedback={allowFeedback}
        />
      ))}

      {pendingQuery && (
        <MessageBubble role={MessageRole.USER} content={pendingQuery} />
      )}

      {streamingAnswer ? (
        <MessageBubble
          role={MessageRole.ASSISTANT}
          content={streamingAnswer.text}
          citations={streamingAnswer.citations}
          streaming
        />
      ) : (
        isSending && (
          <div className="flex gap-3">
            <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-tr from-sky-600 to-indigo-600 text-white shadow-sm">
              <Bot className="h-4 w-4" />
            </span>
            <div className="rounded-2xl rounded-tl-md border bg-card px-3 shadow-sm">
              <TypingIndicator />
            </div>
          </div>
        )
      )}

      <div ref={bottomRef} />
    </div>
  );
}
