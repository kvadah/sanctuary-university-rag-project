'use client';

import { useEffect, useMemo, useState } from 'react';
import { MessagesSquare, PanelLeftClose, PanelLeftOpen } from 'lucide-react';
import { ConversationSidebar } from '@/components/chat/conversation-sidebar';
import { MessageList } from '@/components/chat/message-list';
import { ChatComposer } from '@/components/chat/chat-composer';
import { EmptyChat } from '@/components/chat/empty-chat';
import { Button } from '@/components/ui/button';
import { Spinner } from '@/components/ui/spinner';
import { useConversation } from '@/hooks/use-conversations';
import { useChatStream } from '@/hooks/use-chat';
import { useToast } from '@/hooks/use-toast';
import { usePersistentBoolean } from '@/hooks/use-persistent-boolean';

export default function ChatPage() {
  const [activeId, setActiveId] = useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  // Conversation history rail collapses on desktop; expanded by default.
  const [historyCollapsed, setHistoryCollapsed] = usePersistentBoolean(
    'chat-history-collapsed',
    false,
  );

  const conversation = useConversation(activeId);
  const { turn, displayText, isStreaming, send, reset } = useChatStream();
  const { error: toastError } = useToast();

  const serverMessages = useMemo(
    () => conversation.data?.messages ?? [],
    [conversation.data],
  );

  // Once the streamed answer is persisted and shows up in server history, drop
  // the live turn so we don't render it twice.
  const turnPersisted =
    Boolean(turn?.messageId) &&
    serverMessages.some((m) => m.id === turn!.messageId);

  useEffect(() => {
    if (turnPersisted) reset();
  }, [turnPersisted, reset]);

  // The live turn is shown until its assistant message lands in server history.
  const showLiveTurn = Boolean(turn) && !turnPersisted;
  const pendingQuery = showLiveTurn ? turn!.query : null;
  const streamingAnswer =
    showLiveTurn && displayText
      ? { text: displayText, citations: turn!.citations }
      : null;
  // Waiting for the first token: show the typing indicator, not an empty bubble.
  const isSending = showLiveTurn && !displayText;

  const handleSend = (query: string, academicTerm: string | null) => {
    send(
      { conversation_id: activeId, query, academic_term: academicTerm },
      {
        onConversation: (id) => setActiveId(id),
        onError: (message) => toastError('Message failed', message),
      },
    );
  };

  const handleSelect = (id: string) => {
    setActiveId(id);
    reset();
    setDrawerOpen(false);
  };

  const handleNew = () => {
    setActiveId(null);
    reset();
    setDrawerOpen(false);
  };

  const loadingHistory =
    Boolean(activeId) && conversation.isLoading && serverMessages.length === 0;
  const hasContent = serverMessages.length > 0 || showLiveTurn;
  const showEmpty = !loadingHistory && !hasContent;

  return (
    <div className="flex h-full">
      {/* Desktop conversation rail — hidden while collapsed */}
      {!historyCollapsed && (
        <aside className="hidden w-72 shrink-0 border-r bg-card md:flex md:flex-col">
          <ConversationSidebar
            activeId={activeId}
            onSelect={handleSelect}
            onNew={handleNew}
          />
        </aside>
      )}

      {/* Mobile conversation drawer */}
      {drawerOpen && (
        <div className="fixed inset-0 z-40 flex md:hidden">
          <button
            type="button"
            aria-label="Close conversations"
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={() => setDrawerOpen(false)}
          />
          <div className="relative flex w-72 max-w-[80%] flex-col border-r bg-card shadow-xl animate-slide-in-left">
            <ConversationSidebar
              activeId={activeId}
              onSelect={handleSelect}
              onNew={handleNew}
            />
          </div>
        </div>
      )}

      {/* Conversation column */}
      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex items-center gap-2 border-b px-4 py-2">
          {/* Mobile: open the conversation drawer */}
          <Button
            variant="outline"
            size="sm"
            className="md:hidden"
            onClick={() => setDrawerOpen(true)}
          >
            <MessagesSquare className="h-4 w-4" />
            Conversations
          </Button>

          {/* Desktop: collapse/expand the conversation rail */}
          <Button
            variant="outline"
            size="sm"
            className="hidden md:inline-flex"
            aria-pressed={!historyCollapsed}
            onClick={() => setHistoryCollapsed((c) => !c)}
          >
            {historyCollapsed ? (
              <PanelLeftOpen className="h-4 w-4" />
            ) : (
              <PanelLeftClose className="h-4 w-4" />
            )}
            {historyCollapsed ? 'Show conversations' : 'Hide conversations'}
          </Button>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto scrollbar-thin">
          {loadingHistory ? (
            <div className="flex h-full items-center justify-center">
              <Spinner className="h-6 w-6" />
            </div>
          ) : showEmpty ? (
            <div className="flex min-h-full items-center justify-center">
              <EmptyChat onPick={(q) => handleSend(q, null)} />
            </div>
          ) : (
            <MessageList
              messages={serverMessages}
              conversationId={activeId}
              pendingQuery={pendingQuery}
              streamingAnswer={streamingAnswer}
              isSending={isSending}
            />
          )}
        </div>

        <ChatComposer onSend={handleSend} disabled={isStreaming} />
      </div>
    </div>
  );
}
