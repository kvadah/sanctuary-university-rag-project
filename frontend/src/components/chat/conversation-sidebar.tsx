'use client';

import { MessageSquare, Plus } from 'lucide-react';
import { useConversations } from '@/hooks/use-conversations';
import { cn, formatRelative } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Spinner } from '@/components/ui/spinner';

interface ConversationSidebarProps {
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
}

export function ConversationSidebar({
  activeId,
  onSelect,
  onNew,
}: ConversationSidebarProps) {
  const { data, isLoading } = useConversations();
  const items = data?.items ?? [];

  return (
    <div className="flex h-full flex-col">
      <div className="p-3">
        <Button className="w-full" onClick={onNew}>
          <Plus className="h-4 w-4" />
          New chat
        </Button>
      </div>
      <div className="flex-1 overflow-y-auto px-2 pb-3 scrollbar-thin">
        {isLoading ? (
          <div className="flex justify-center py-6">
            <Spinner />
          </div>
        ) : items.length === 0 ? (
          <p className="px-3 py-6 text-center text-xs text-muted-foreground">
            No conversations yet.
          </p>
        ) : (
          <ul className="space-y-0.5">
            {items.map((c) => (
              <li key={c.id}>
                <button
                  type="button"
                  onClick={() => onSelect(c.id)}
                  className={cn(
                    'flex w-full items-start gap-2 rounded-lg px-3 py-2 text-left transition-colors',
                    activeId === c.id
                      ? 'bg-primary/10 text-primary'
                      : 'text-foreground hover:bg-muted',
                  )}
                >
                  <MessageSquare className="mt-0.5 h-4 w-4 shrink-0 opacity-70" />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm font-medium">
                      {c.title || 'Untitled conversation'}
                    </span>
                    <span className="block text-xs text-muted-foreground">
                      {formatRelative(c.updated_at)}
                    </span>
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
