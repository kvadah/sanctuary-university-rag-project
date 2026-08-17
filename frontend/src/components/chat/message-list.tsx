'use client';

import { useEffect, useRef } from 'react';
import { Bot } from 'lucide-react';
import { Message, MessageRole } from '@/lib/types';
import { getCitations } from '@/lib/utils';
import { MessageBubble } from './message-bubble';
import { TypingIndicator } from './typing-indicator';

interface MessageListProps {
  messages: Message[];
  conversationId?: string | null;
  pendingQuery?: string | null;
  isSending?: boolean;
}

export function MessageList({
  messages,
  conversationId,
  pendingQuery,
  isSending,
}: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length, pendingQuery, isSending]);

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
        />
      ))}

      {pendingQuery && (
        <MessageBubble role={MessageRole.USER} content={pendingQuery} />
      )}

      {isSending && (
        <div className="flex gap-3">
          <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-tr from-sky-600 to-indigo-600 text-white shadow-sm">
            <Bot className="h-4 w-4" />
          </span>
          <div className="rounded-2xl rounded-tl-md border bg-card px-3 shadow-sm">
            <TypingIndicator />
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
