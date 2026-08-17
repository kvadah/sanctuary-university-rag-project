import { FileText } from 'lucide-react';
import { Citation } from '@/lib/types';

export function CitationCard({ citation }: { citation: Citation }) {
  return (
    <div className="rounded-xl border bg-background/60 p-3 text-left transition-colors hover:border-primary/40">
      <div className="flex items-start gap-2">
        <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-[11px] font-semibold text-primary">
          {citation.index}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5">
            <FileText className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
            <p className="truncate text-sm font-medium text-foreground">
              {citation.document_title}
            </p>
          </div>
          <p className="mt-1 line-clamp-3 text-xs leading-relaxed text-muted-foreground">
            {citation.snippet}
          </p>
          <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-0.5 text-[11px] text-muted-foreground">
            {citation.page_number != null && (
              <span>Page {citation.page_number}</span>
            )}
            {citation.section_title && (
              <span className="truncate">{citation.section_title}</span>
            )}
            <span>{Math.round(citation.score * 100)}% match</span>
          </div>
        </div>
      </div>
    </div>
  );
}
