'use client';

import { MessageSquare, PanelLeftClose, Plus } from 'lucide-react';
import { useConversations } from '@/hooks/use-conversations';
import { cn, formatRelative } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Spinner } from '@/components/ui/spinner';

interface ConversationSidebarProps {
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  /** Collapse the conversation rail (desktop) or close the drawer (mobile). */
  onCollapse?: () => void;
}

export function ConversationSidebar({
  activeId,
  onSelect,
  onNew,
  onCollapse,
}: ConversationSidebarProps) {
  const { data, isLoading } = useConversations();
  const items = data?.items ?? [];

  return (
    <div className="flex h-full flex-col">
      <div className="space-y-2 p-3">
        {onCollapse && (
          <div className="flex justify-end">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-muted-foreground hover:text-foreground"
              onClick={onCollapse}
              aria-label="Hide conversations"
              title="Hide conversations"
            >
              <PanelLeftClose className="h-4 w-4" />
            </Button>
          </div>
        )}
        <Button
          className="w-full gap-2 rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-sm shadow-brand-600/20 transition-all hover:from-brand-600 hover:to-brand-700 hover:shadow-md hover:shadow-brand-600/30 active:scale-[0.98]"
          onClick={onNew}
        >
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
