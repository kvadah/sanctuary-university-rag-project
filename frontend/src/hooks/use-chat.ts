'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { chatApi } from '@/lib/api';
import { ChatQueryRequest, Citation } from '@/lib/types';
import { conversationKeys } from './use-conversations';

/** The in-flight (not-yet-persisted) chat turn being streamed. */
export interface LiveTurn {
  query: string;
  streamText: string;
  citations: Citation[];
  conversationId: string | null;
  messageId: string | null;
  done: boolean;
}

interface SendOptions {
  /** Called with the new conversation id when a brand-new conversation is created. */
  onConversation?: (id: string) => void;
  onError?: (message: string) => void;
}

/**
 * Drive a streaming chat turn over SSE. Exposes the growing `turn` plus a
 * `displayText` that reveals characters gradually (Gemini often sends the whole
 * answer in one chunk, so this keeps the "typing" feel). On completion it
 * invalidates the conversation queries so the persisted history takes over.
 */
export function useChatStream() {
  const queryClient = useQueryClient();
  const [turn, setTurn] = useState<LiveTurn | null>(null);
  const [displayText, setDisplayText] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  // Typewriter reveal: catch `displayText` up to `turn.streamText` a few chars
  // per frame; snap to the full text once the stream is done.
  const targetRef = useRef('');
  const doneRef = useRef(false);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    targetRef.current = turn?.streamText ?? '';
    doneRef.current = turn?.done ?? false;

    if (!turn) {
      if (rafRef.current != null) cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
      setDisplayText('');
      return;
    }

    if (rafRef.current != null) return; // loop already running
    const tick = () => {
      rafRef.current = null;
      setDisplayText((cur) => {
        const target = targetRef.current;
        if (cur.length >= target.length) return cur; // caught up → loop stops
        const remaining = target.length - cur.length;
        const step = doneRef.current ? remaining : Math.max(1, Math.ceil(remaining / 10));
        const next = target.slice(0, cur.length + step);
        if (next.length < target.length) rafRef.current = requestAnimationFrame(tick);
        return next;
      });
    };
    rafRef.current = requestAnimationFrame(tick);
  }, [turn]);

  // Cancel any in-flight request / animation on unmount.
  useEffect(
    () => () => {
      abortRef.current?.abort();
      if (rafRef.current != null) cancelAnimationFrame(rafRef.current);
    },
    [],
  );

  const reset = useCallback(() => {
    setTurn(null);
    setIsStreaming(false);
  }, []);

  const send = useCallback(
    (body: ChatQueryRequest, opts?: SendOptions) => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      let convId = body.conversation_id ?? null;
      setIsStreaming(true);
      setDisplayText('');
      setTurn({
        query: body.query,
        streamText: '',
        citations: [],
        conversationId: convId,
        messageId: null,
        done: false,
      });

      chatApi
        .queryStream(
          body,
          {
            onMeta: ({ conversation_id, citations }) => {
              convId = conversation_id;
              setTurn((t) => (t ? { ...t, conversationId: conversation_id, citations } : t));
              if (!body.conversation_id) opts?.onConversation?.(conversation_id);
            },
            onDelta: (text) => {
              setTurn((t) => (t ? { ...t, streamText: t.streamText + text } : t));
            },
            onDone: ({ message_id }) => {
              setTurn((t) => (t ? { ...t, messageId: message_id, done: true } : t));
              setIsStreaming(false);
              queryClient.invalidateQueries({ queryKey: conversationKeys.all });
              if (convId) {
                queryClient.invalidateQueries({
                  queryKey: conversationKeys.detail(convId),
                });
              }
            },
            onError: (message) => {
              setIsStreaming(false);
              reset();
              opts?.onError?.(message);
            },
          },
          controller.signal,
        )
        .catch((err) => {
          if (controller.signal.aborted) return;
          setIsStreaming(false);
          reset();
          opts?.onError?.(
            err instanceof Error ? err.message : 'Message failed. Please try again.',
          );
        });
    },
    [queryClient, reset],
  );

  return { turn, displayText, isStreaming, send, reset };
}
