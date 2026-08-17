'use client';

import { useState } from 'react';
import { Library, Plus } from 'lucide-react';
import { RoleGuard } from '@/components/layout/role-guard';
import { SourceTable } from '@/components/knowledge/source-table';
import { SourceFormDialog } from '@/components/knowledge/source-form-dialog';
import { DeleteConfirmDialog } from '@/components/knowledge/delete-confirm-dialog';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { EmptyState } from '@/components/ui/empty-state';
import { Pagination } from '@/components/ui/pagination';
import { useKnowledgeSources } from '@/hooks/use-knowledge-sources';
import { KnowledgeSource, UserRole } from '@/lib/types';
import { extractError } from '@/lib/utils';

function KnowledgeSourcesInner() {
  const [page, setPage] = useState(1);
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<KnowledgeSource | null>(null);
  const [deleting, setDeleting] = useState<KnowledgeSource | null>(null);

  const { data, isLoading, isError, error } = useKnowledgeSources(page);
  const sources = data?.items ?? [];
  const totalPages = data?.pagination.total_pages ?? 1;

  const openCreate = () => {
    setEditing(null);
    setFormOpen(true);
  };
  const openEdit = (source: KnowledgeSource) => {
    setEditing(source);
    setFormOpen(true);
  };

  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-6 sm:px-6 lg:px-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Knowledge Sources
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Connectors the ingestion pipeline syncs content from
            {data ? ` · ${data.pagination.total_items} total` : ''}.
          </p>
        </div>
        <Button onClick={openCreate}>
          <Plus className="h-4 w-4" />
          New source
        </Button>
      </div>

      <div className="mt-6">
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-16 w-full rounded-2xl" />
            ))}
          </div>
        ) : isError ? (
          <EmptyState
            icon={Library}
            title="Couldn’t load sources"
            description={extractError(error, 'Please try again shortly.')}
          />
        ) : sources.length === 0 ? (
          <EmptyState
            icon={Library}
            title="No knowledge sources yet"
            description="Add a connector to organize where documents come from."
            action={
              <Button onClick={openCreate}>
                <Plus className="h-4 w-4" />
                New source
              </Button>
            }
          />
        ) : (
          <div className="space-y-4">
            <SourceTable
              sources={sources}
              onEdit={openEdit}
              onDelete={setDeleting}
            />
            <Pagination
              page={page}
              totalPages={totalPages}
              onPageChange={setPage}
            />
          </div>
        )}
      </div>

      <SourceFormDialog
        open={formOpen}
        onClose={() => setFormOpen(false)}
        source={editing}
      />
      <DeleteConfirmDialog
        source={deleting}
        onClose={() => setDeleting(null)}
      />
    </div>
  );
}

export default function KnowledgeSourcesPage() {
  return (
    <RoleGuard roles={[UserRole.ADMIN]}>
      <KnowledgeSourcesInner />
    </RoleGuard>
  );
}
