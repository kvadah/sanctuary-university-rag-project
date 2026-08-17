'use client';

import { Pencil, Trash2, Library } from 'lucide-react';
import { KnowledgeSource } from '@/lib/types';
import { formatDate, formatRelative, titleCase } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { SyncStatusBadge } from './sync-status-badge';

interface SourceTableProps {
  sources: KnowledgeSource[];
  onEdit: (source: KnowledgeSource) => void;
  onDelete: (source: KnowledgeSource) => void;
}

export function SourceTable({ sources, onEdit, onDelete }: SourceTableProps) {
  return (
    <div className="overflow-hidden rounded-2xl border bg-card">
      <table className="hidden w-full text-sm md:table">
        <thead>
          <tr className="border-b bg-muted/40 text-left text-xs uppercase tracking-wide text-muted-foreground">
            <th className="px-4 py-3 font-medium">Source</th>
            <th className="px-4 py-3 font-medium">Type</th>
            <th className="px-4 py-3 font-medium">Status</th>
            <th className="px-4 py-3 font-medium">Last synced</th>
            <th className="px-4 py-3 text-right font-medium">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {sources.map((s) => (
            <tr key={s.id} className="transition-colors hover:bg-muted/30">
              <td className="px-4 py-3">
                <div className="flex items-center gap-3">
                  <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                    <Library className="h-4 w-4" />
                  </span>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="truncate font-medium text-foreground">
                        {s.name}
                      </p>
                      {!s.is_active && (
                        <Badge variant="secondary">Inactive</Badge>
                      )}
                    </div>
                    {s.description && (
                      <p className="truncate text-xs text-muted-foreground">
                        {s.description}
                      </p>
                    )}
                  </div>
                </div>
              </td>
              <td className="px-4 py-3 text-muted-foreground">
                {titleCase(s.source_type)}
              </td>
              <td className="px-4 py-3">
                <SyncStatusBadge status={s.sync_status} />
              </td>
              <td className="px-4 py-3 text-muted-foreground">
                {s.last_synced_at ? formatDate(s.last_synced_at) : 'Never'}
              </td>
              <td className="px-4 py-3">
                <div className="flex items-center justify-end gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={() => onEdit(s)}
                    aria-label={`Edit ${s.name}`}
                  >
                    <Pencil className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-destructive hover:bg-destructive/10 hover:text-destructive"
                    onClick={() => onDelete(s)}
                    aria-label={`Delete ${s.name}`}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Mobile stacked cards */}
      <ul className="divide-y divide-border md:hidden">
        {sources.map((s) => (
          <li key={s.id} className="p-4">
            <div className="flex items-start gap-3">
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <Library className="h-4 w-4" />
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <p className="truncate font-medium text-foreground">
                    {s.name}
                  </p>
                  {!s.is_active && <Badge variant="secondary">Inactive</Badge>}
                </div>
                {s.description && (
                  <p className="truncate text-xs text-muted-foreground">
                    {s.description}
                  </p>
                )}
                <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1">
                  <span className="text-xs text-muted-foreground">
                    {titleCase(s.source_type)}
                  </span>
                  <SyncStatusBadge status={s.sync_status} />
                  <span className="text-xs text-muted-foreground">
                    {s.last_synced_at
                      ? formatRelative(s.last_synced_at)
                      : 'Never synced'}
                  </span>
                </div>
              </div>
            </div>
            <div className="mt-3 flex justify-end gap-2">
              <Button variant="outline" size="sm" onClick={() => onEdit(s)}>
                <Pencil className="h-4 w-4" />
                Edit
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="text-destructive hover:bg-destructive/10 hover:text-destructive"
                onClick={() => onDelete(s)}
              >
                <Trash2 className="h-4 w-4" />
                Delete
              </Button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
