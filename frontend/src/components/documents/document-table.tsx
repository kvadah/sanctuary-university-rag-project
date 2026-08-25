'use client';

import { FileText, Loader2 } from 'lucide-react';
import { Document, IndexingJob, IndexingStatus } from '@/lib/types';
import { formatDate } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { ClassificationBadge } from './classification-badge';
import { IndexingStatusBadge } from './indexing-status-badge';

const SPINNING = [IndexingStatus.PENDING, IndexingStatus.PROCESSING];

export function DocumentTable({
  documents,
  jobs = [],
}: {
  documents: Document[];
  jobs?: IndexingJob[];
}) {
  return (
    <div className="overflow-hidden rounded-2xl border bg-card">
      {/* Desktop / tablet table */}
      <table className="hidden w-full text-sm sm:table">
        <thead>
          <tr className="border-b bg-muted/40 text-left text-xs uppercase tracking-wide text-muted-foreground">
            <th className="px-4 py-3 font-medium">Document</th>
            <th className="px-4 py-3 font-medium">Access</th>
            <th className="px-4 py-3 font-medium">Type</th>
            <th className="px-4 py-3 font-medium">Term</th>
            <th className="px-4 py-3 font-medium">Added</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {jobs.map((job) => {
            const spinning = SPINNING.includes(job.status);
            return (
              <tr key={job.id} className="bg-muted/20">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-muted text-muted-foreground">
                      {spinning ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <FileText className="h-4 w-4" />
                      )}
                    </span>
                    <div className="min-w-0">
                      <p className="truncate font-medium text-foreground">
                        {job.original_filename ?? 'Untitled upload'}
                      </p>
                      {job.status === IndexingStatus.FAILED &&
                        job.error_message && (
                          <span className="line-clamp-1 text-xs text-rose-600 dark:text-rose-300">
                            {job.error_message}
                          </span>
                        )}
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3" colSpan={3}>
                  <IndexingStatusBadge status={job.status} />
                </td>
                <td className="px-4 py-3 text-muted-foreground">
                  {formatDate(job.created_at)}
                </td>
              </tr>
            );
          })}
          {documents.map((doc) => (
            <tr key={doc.id} className="transition-colors hover:bg-muted/30">
              <td className="px-4 py-3">
                <div className="flex items-center gap-3">
                  <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                    <FileText className="h-4 w-4" />
                  </span>
                  <div className="min-w-0">
                    <p className="truncate font-medium text-foreground">
                      {doc.title}
                    </p>
                    {!doc.is_current && (
                      <span className="text-xs text-muted-foreground">
                        Superseded version
                      </span>
                    )}
                  </div>
                </div>
              </td>
              <td className="px-4 py-3">
                <ClassificationBadge classification={doc.classification} />
              </td>
              <td className="px-4 py-3 uppercase text-muted-foreground">
                {doc.file_type || '—'}
              </td>
              <td className="px-4 py-3 text-muted-foreground">
                {doc.academic_term || '—'}
              </td>
              <td className="px-4 py-3 text-muted-foreground">
                {formatDate(doc.created_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Mobile stacked cards */}
      <ul className="divide-y divide-border sm:hidden">
        {jobs.map((job) => {
          const spinning = SPINNING.includes(job.status);
          return (
            <li key={job.id} className="flex items-start gap-3 bg-muted/20 p-4">
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-muted text-muted-foreground">
                {spinning ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <FileText className="h-4 w-4" />
                )}
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium text-foreground">
                  {job.original_filename ?? 'Untitled upload'}
                </p>
                <div className="mt-1.5">
                  <IndexingStatusBadge status={job.status} />
                </div>
                {job.status === IndexingStatus.FAILED && job.error_message && (
                  <p className="mt-1 line-clamp-2 text-xs text-rose-600 dark:text-rose-300">
                    {job.error_message}
                  </p>
                )}
              </div>
            </li>
          );
        })}
        {documents.map((doc) => (
          <li key={doc.id} className="flex items-start gap-3 p-4">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <FileText className="h-4 w-4" />
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate font-medium text-foreground">{doc.title}</p>
              <div className="mt-1.5 flex flex-wrap items-center gap-2">
                <ClassificationBadge classification={doc.classification} />
                {doc.academic_term && (
                  <Badge variant="secondary">{doc.academic_term}</Badge>
                )}
                <span className="text-xs uppercase text-muted-foreground">
                  {doc.file_type}
                </span>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                Added {formatDate(doc.created_at)}
              </p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
