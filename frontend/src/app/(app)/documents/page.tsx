'use client';

import { useState } from 'react';
import { FileText, UploadCloud } from 'lucide-react';
import { DocumentTable } from '@/components/documents/document-table';
import { UploadDialog } from '@/components/documents/upload-dialog';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { EmptyState } from '@/components/ui/empty-state';
import { Pagination } from '@/components/ui/pagination';
import { useDocuments, useIndexingJobs } from '@/hooks/use-documents';
import { useAuthStore } from '@/stores/auth-store';
import { UPLOAD_ROLES } from '@/lib/constants';
import { IndexingStatus } from '@/lib/types';
import { extractError } from '@/lib/utils';

export default function DocumentsPage() {
  const [page, setPage] = useState(1);
  const [uploadOpen, setUploadOpen] = useState(false);
  const user = useAuthStore((s) => s.user);
  const { data, isLoading, isError, error } = useDocuments(page);

  const canUpload = user ? UPLOAD_ROLES.includes(user.role) : false;
  const { data: jobs } = useIndexingJobs(canUpload);
  const documents = data?.items ?? [];
  const totalPages = data?.pagination.total_pages ?? 1;

  // Surface in-flight and recently-failed jobs as rows above the catalog, only on
  // the first page (a completed job disappears once its document is listed).
  const visibleJobs =
    page === 1
      ? (jobs ?? []).filter((j) => j.status !== IndexingStatus.COMPLETED)
      : [];

  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-6 sm:px-6 lg:px-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Documents
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            The knowledge base the assistant retrieves from
            {data ? ` · ${data.pagination.total_items} total` : ''}.
          </p>
        </div>
        {canUpload && user && (
          <Button onClick={() => setUploadOpen(true)}>
            <UploadCloud className="h-4 w-4" />
            Upload document
          </Button>
        )}
      </div>

      <div className="mt-6">
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-16 w-full rounded-2xl" />
            ))}
          </div>
        ) : isError ? (
          <EmptyState
            icon={FileText}
            title="Couldn’t load documents"
            description={extractError(error, 'Please try again shortly.')}
          />
        ) : documents.length === 0 && visibleJobs.length === 0 ? (
          <EmptyState
            icon={FileText}
            title="No documents yet"
            description={
              canUpload
                ? 'Upload your first document to start building the knowledge base.'
                : 'No documents are available to you yet.'
            }
            action={
              canUpload ? (
                <Button onClick={() => setUploadOpen(true)}>
                  <UploadCloud className="h-4 w-4" />
                  Upload document
                </Button>
              ) : undefined
            }
          />
        ) : (
          <div className="space-y-4">
            <DocumentTable documents={documents} jobs={visibleJobs} />
            <Pagination
              page={page}
              totalPages={totalPages}
              onPageChange={setPage}
            />
          </div>
        )}
      </div>

      {user && (
        <UploadDialog
          open={uploadOpen}
          onClose={() => setUploadOpen(false)}
          role={user.role}
        />
      )}
    </div>
  );
}
