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
import { useSendMessage } from '@/hooks/use-chat';
import { useToast } from '@/hooks/use-toast';
import { usePersistentBoolean } from '@/hooks/use-persistent-boolean';
import { ChatQueryResponse, Message, MessageRole } from '@/lib/types';
import { extractError } from '@/lib/utils';

interface Optimistic {
  query: string;
  response: ChatQueryResponse | null;
}

export default function ChatPage() {
  const [activeId, setActiveId] = useState<string | null>(null);
  const [optimistic, setOptimistic] = useState<Optimistic | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  // Conversation history rail collapses on desktop; expanded by default.
  const [historyCollapsed, setHistoryCollapsed] = usePersistentBoolean(
    'chat-history-collapsed',
    false,
  );

  const conversation = useConversation(activeId);
  const send = useSendMessage();
  const { error: toastError } = useToast();

  const serverMessages = useMemo(
    () => conversation.data?.messages ?? [],
    [conversation.data],
  );

  // Once the server history includes the just-sent answer, drop the optimistic
  // pair so we don't render it twice.
  useEffect(() => {
    if (
      optimistic?.response &&
      serverMessages.some((m) => m.id === optimistic.response!.message_id)
    ) {
      setOptimistic(null);
    }
  }, [serverMessages, optimistic]);

  // Compose what to render: server history plus any not-yet-persisted turn.
  const { messages, isSending } = useMemo(() => {
    const list: Message[] = [...serverMessages];
    let sending = false;

    if (optimistic) {
      const persisted =
        optimistic.response &&
        serverMessages.some((m) => m.id === optimistic.response!.message_id);

      if (!persisted) {
        list.push({
          id: 'optimistic-user',
          conversation_id: activeId ?? 'pending',
          role: MessageRole.USER,
          content: optimistic.query,
          citations: null,
          created_at: '',
        });

        if (optimistic.response) {
          list.push({
            id: optimistic.response.message_id,
            conversation_id: optimistic.response.conversation_id,
            role: MessageRole.ASSISTANT,
            content: optimistic.response.answer,
            citations: { items: optimistic.response.citations },
            created_at: '',
          });
        } else {
          sending = true;
        }
      }
    }

    return { messages: list, isSending: sending };
  }, [serverMessages, optimistic, activeId]);

  const handleSend = (query: string, academicTerm: string | null) => {
    setOptimistic({ query, response: null });
    send.mutate(
      { conversation_id: activeId, query, academic_term: academicTerm },
      {
        onSuccess: (data) => {
          if (!activeId) setActiveId(data.conversation_id);
          setOptimistic({ query, response: data });
        },
        onError: (err) => {
          setOptimistic(null);
          toastError('Message failed', extractError(err, 'Please try again.'));
        },
      },
    );
  };

  const handleSelect = (id: string) => {
    setActiveId(id);
    setOptimistic(null);
    setDrawerOpen(false);
  };

  const handleNew = () => {
    setActiveId(null);
    setOptimistic(null);
    setDrawerOpen(false);
  };

  const loadingHistory =
    Boolean(activeId) && conversation.isLoading && messages.length === 0;
  const showEmpty = !loadingHistory && messages.length === 0 && !isSending;

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
              messages={messages}
              conversationId={activeId}
              isSending={isSending}
            />
          )}
        </div>

        <ChatComposer onSend={handleSend} disabled={send.isPending} />
      </div>
    </div>
  );
}
