import { Fragment } from 'react';
import { Bot } from 'lucide-react';
import { Citation, MessageRole } from '@/lib/types';
import { cn } from '@/lib/utils';
import { CitationCard } from './citation-card';
import { FeedbackButtons } from './feedback-buttons';

/**
 * Render answer text as React nodes (never innerHTML, so it's XSS-safe).
 * Supports **bold**, `code`, and [n] citation chips; other text is escaped by React.
 */
function renderInline(text: string, citedIndexes: Set<number>): React.ReactNode[] {
  const nodes: React.ReactNode[] = [];
  const regex = /(\*\*[^*]+\*\*|`[^`]+`|\[\d+\])/g;
  let last = 0;
  let key = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > last) nodes.push(text.slice(last, match.index));
    const token = match[0];
    if (token.startsWith('**')) {
      nodes.push(<strong key={key++}>{token.slice(2, -2)}</strong>);
    } else if (token.startsWith('`')) {
      nodes.push(
        <code
          key={key++}
          className="rounded bg-muted px-1 py-0.5 font-mono text-[0.85em]"
        >
          {token.slice(1, -1)}
        </code>,
      );
    } else {
      const n = Number(token.slice(1, -1));
      if (citedIndexes.has(n)) {
        nodes.push(
          <sup
            key={key++}
            className="mx-0.5 inline-flex h-4 min-w-4 items-center justify-center rounded bg-primary/15 px-1 text-[10px] font-semibold text-primary"
          >
            {n}
          </sup>,
        );
      } else {
        nodes.push(token);
      }
    }
    last = regex.lastIndex;
  }
  if (last < text.length) nodes.push(text.slice(last));
  return nodes;
}

function RichText({
  content,
  citedIndexes,
}: {
  content: string;
  citedIndexes: Set<number>;
}) {
  const paragraphs = content.split(/\n{2,}/);
  return (
    <>
      {paragraphs.map((para, pi) => (
        <p key={pi} className={cn(pi > 0 && 'mt-3')}>
          {para.split('\n').map((line, li) => (
            <Fragment key={li}>
              {li > 0 && <br />}
              {renderInline(line, citedIndexes)}
            </Fragment>
          ))}
        </p>
      ))}
    </>
  );
}

interface MessageBubbleProps {
  role: MessageRole;
  content: string;
  citations?: Citation[];
  messageId?: string;
  conversationId?: string | null;
}

export function MessageBubble({
  role,
  content,
  citations = [],
  messageId,
  conversationId,
}: MessageBubbleProps) {
  const isUser = role === MessageRole.USER;

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-br-md bg-primary px-4 py-2.5 text-sm text-primary-foreground shadow-sm">
          {content}
        </div>
      </div>
    );
  }

  const citedIndexes = new Set(citations.map((c) => c.index));

  return (
    <div className="flex gap-3">
      <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-tr from-sky-600 to-indigo-600 text-white shadow-sm">
        <Bot className="h-4 w-4" />
      </span>
      <div className="min-w-0 flex-1 space-y-3">
        <div className="rounded-2xl rounded-tl-md border bg-card px-4 py-3 text-sm leading-relaxed text-foreground shadow-sm">
          <RichText content={content} citedIndexes={citedIndexes} />
        </div>

        {citations.length > 0 && (
          <div className="space-y-2">
            <p className="px-1 text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Sources
            </p>
            <div className="grid gap-2 sm:grid-cols-2">
              {citations.map((c) => (
                <CitationCard key={c.chunk_id ?? c.index} citation={c} />
              ))}
            </div>
          </div>
        )}

        {messageId && (
          <div className="flex items-center gap-2 px-1">
            <span className="text-xs text-muted-foreground">
              Was this helpful?
            </span>
            <FeedbackButtons
              messageId={messageId}
              conversationId={conversationId}
            />
          </div>
        )}
      </div>
    </div>
  );
}
