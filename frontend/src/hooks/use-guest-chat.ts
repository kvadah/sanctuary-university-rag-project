'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { chatApi } from '@/lib/api';
import { Citation, Message, MessageRole, PublicChatTurn } from '@/lib/types';

/** The in-flight guest turn being streamed (never persisted). */
interface GuestTurn {
  query: string;
  streamText: string;
  citations: Citation[];
}

interface SendOptions {
  onError?: (message: string) => void;
}

/**
 * Drive an anonymous ("guest") chat entirely in the browser. Unlike
 * {@link useChatStream}, nothing is saved server-side: the completed transcript
 * lives in `messages` state, and each request carries that transcript back as
 * `history` so the model still has multi-turn context. `newChat` abandons the
 * current thread. The typewriter reveal mirrors the authed hook so the two chats
 * feel identical.
 */
export function useGuestChatStream() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [turn, setTurn] = useState<GuestTurn | null>(null);
  const [displayText, setDisplayText] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);

  // Refs mirror state so the stream callbacks read fresh values without being
  // recreated: `messagesRef` builds the history snapshot; `liveRef` accumulates
  // the streaming answer and is committed to the transcript on done.
  const messagesRef = useRef<Message[]>([]);
  const liveRef = useRef<GuestTurn | null>(null);
  const idRef = useRef(0);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  // Typewriter reveal: catch `displayText` up to `turn.streamText` a few chars
  // per frame. On done we clear the live turn (below), which resets this to ''
  // in the same tick the full answer lands in the transcript — so no flicker.
  const targetRef = useRef('');
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    targetRef.current = turn?.streamText ?? '';

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
        const step = Math.max(1, Math.ceil(remaining / 10));
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

  /** Append a finished {question, answer} pair to the local transcript. */
  const commitTurn = useCallback((live: GuestTurn) => {
    const base = idRef.current++;
    const now = new Date().toISOString();
    const userMessage: Message = {
      id: `guest-u-${base}`,
      conversation_id: 'guest',
      role: MessageRole.USER,
      content: live.query,
      citations: null,
      created_at: now,
    };
    const assistantMessage: Message = {
      id: `guest-a-${base}`,
      conversation_id: 'guest',
      role: MessageRole.ASSISTANT,
      content: live.streamText,
      citations: live.citations.length ? { items: live.citations } : null,
      created_at: now,
    };
    setMessages((prev) => [...prev, userMessage, assistantMessage]);
  }, []);

  const send = useCallback(
    (query: string, academicTerm: string | null, opts?: SendOptions) => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      // Snapshot the completed transcript as history BEFORE this turn.
      const history: PublicChatTurn[] = messagesRef.current.map((m) => ({
        role: m.role === MessageRole.USER ? 'user' : 'assistant',
        content: m.content,
      }));

      liveRef.current = { query, streamText: '', citations: [] };
      setTurn({ query, streamText: '', citations: [] });
      setDisplayText('');
      setIsStreaming(true);

      const fail = (message: string) => {
        liveRef.current = null;
        setTurn(null);
        setDisplayText('');
        setIsStreaming(false);
        opts?.onError?.(message);
      };

      chatApi
        .publicQueryStream(
          { query, academic_term: academicTerm, history },
          {
            onMeta: ({ citations }) => {
              if (!liveRef.current) return;
              liveRef.current = { ...liveRef.current, citations };
              setTurn((t) => (t ? { ...t, citations } : t));
            },
            onDelta: (text) => {
              if (!liveRef.current) return;
              liveRef.current = {
                ...liveRef.current,
                streamText: liveRef.current.streamText + text,
              };
              setTurn((t) => (t ? { ...t, streamText: t.streamText + text } : t));
            },
            onDone: () => {
              const live = liveRef.current;
              liveRef.current = null;
              // Move the finished turn into the persistent local transcript and
              // drop the live turn in the same tick (full text is now in messages).
              if (live) commitTurn(live);
              setTurn(null);
              setDisplayText('');
              setIsStreaming(false);
            },
            onError: (message) => fail(message),
          },
          controller.signal,
        )
        .catch((err) => {
          if (controller.signal.aborted) return;
          fail(err instanceof Error ? err.message : 'Message failed. Please try again.');
        });
    },
    [commitTurn],
  );

  /** Abandon the current thread and start fresh — clears the in-browser transcript. */
  const newChat = useCallback(() => {
    abortRef.current?.abort();
    liveRef.current = null;
    setTurn(null);
    setDisplayText('');
    setIsStreaming(false);
    setMessages([]);
  }, []);

  return { messages, turn, displayText, isStreaming, send, newChat };
}
