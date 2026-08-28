'use client';

import Link from 'next/link';
import { BookOpen, Plus } from 'lucide-react';
import { MessageList } from '@/components/chat/message-list';
import { ChatComposer } from '@/components/chat/chat-composer';
import { EmptyChat } from '@/components/chat/empty-chat';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { Button } from '@/components/ui/button';
import { useGuestChatStream } from '@/hooks/use-guest-chat';
import { useToast } from '@/hooks/use-toast';
import { useAuthStore } from '@/stores/auth-store';
import { APP_NAME } from '@/lib/constants';

/**
 * Public "ask without an account" page. Lives outside the `(app)` route group so
 * it is not wrapped in `AuthGuard` — a visitor can ask questions and get cited
 * answers with no login. Nothing is persisted; "New chat" abandons the thread.
 */
export default function AskPage() {
  const { messages, turn, displayText, isStreaming, send, newChat } =
    useGuestChatStream();
  const { error: toastError } = useToast();

  const token = useAuthStore((s) => s.token);
  const hasHydrated = useAuthStore((s) => s.hasHydrated);
  const authed = hasHydrated && Boolean(token);

  const handleSend = (query: string, academicTerm: string | null) => {
    send(query, academicTerm, {
      onError: (message) => toastError('Message failed', message),
    });
  };

  const showLiveTurn = Boolean(turn);
  const pendingQuery = showLiveTurn ? turn!.query : null;
  const streamingAnswer =
    showLiveTurn && displayText
      ? { text: displayText, citations: turn!.citations }
      : null;
  // Waiting for the first token: show the typing indicator, not an empty bubble.
  const isSending = showLiveTurn && !displayText;
  const hasContent = messages.length > 0 || showLiveTurn;

  return (
    <div className="flex h-screen flex-col bg-background">
      {/* Guest header */}
      <header className="flex items-center justify-between gap-3 border-b border-border bg-background/80 px-4 py-2.5 backdrop-blur-md sm:px-6">
        <Link href="/" className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-sky-600 to-indigo-600 text-white shadow-md shadow-sky-500/20">
            <BookOpen className="h-5 w-5" />
          </div>
          <span className="hidden text-base font-bold tracking-tight text-foreground sm:block">
            {APP_NAME}
          </span>
          <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
            Guest
          </span>
        </Link>

        <div className="flex items-center gap-1.5 sm:gap-2">
          <Button variant="outline" size="sm" onClick={newChat}>
            <Plus className="h-4 w-4" />
            New chat
          </Button>
          <ThemeToggle />
          {authed ? (
            <Link
              href="/chat"
              className="inline-flex items-center rounded-lg bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground shadow-sm transition-colors hover:bg-primary/90"
            >
              Your chat
            </Link>
          ) : (
            <>
              <Link
                href="/login"
                className="hidden px-3 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground sm:inline-flex"
              >
                Sign in
              </Link>
              <Link
                href="/register"
                className="inline-flex items-center rounded-lg bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground shadow-sm transition-colors hover:bg-primary/90"
              >
                Get started
              </Link>
            </>
          )}
        </div>
      </header>

      {/* Guest notice — conversations aren't saved */}
      <div className="border-b border-border bg-muted/40 px-4 py-1.5 text-center text-xs text-muted-foreground sm:px-6">
        You’re chatting as a guest — conversations aren’t saved.{' '}
        <Link
          href="/register"
          className="font-medium text-primary underline-offset-2 hover:underline"
        >
          Create an account
        </Link>{' '}
        to keep your history.
      </div>

      {/* Conversation area */}
      <div className="min-h-0 flex-1 overflow-y-auto scrollbar-thin">
        {!hasContent ? (
          <div className="flex min-h-full items-center justify-center">
            <EmptyChat onPick={(q) => handleSend(q, null)} />
          </div>
        ) : (
          <MessageList
            messages={messages}
            pendingQuery={pendingQuery}
            streamingAnswer={streamingAnswer}
            isSending={isSending}
            allowFeedback={false}
          />
        )}
      </div>

      <ChatComposer onSend={handleSend} disabled={isStreaming} />
    </div>
  );
}
