'use client';

import { FileText } from 'lucide-react';
import { Document } from '@/lib/types';
import { formatDate } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { ClassificationBadge } from './classification-badge';

export function DocumentTable({ documents }: { documents: Document[] }) {
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
