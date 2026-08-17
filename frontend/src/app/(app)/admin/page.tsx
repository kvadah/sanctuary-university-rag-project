'use client';

import { FileText, Library, CheckCircle2, AlertTriangle } from 'lucide-react';
import { RoleGuard } from '@/components/layout/role-guard';
import { ClassificationBadge } from '@/components/documents/classification-badge';
import { SyncStatusBadge } from '@/components/knowledge/sync-status-badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { useDocuments } from '@/hooks/use-documents';
import { useKnowledgeSources } from '@/hooks/use-knowledge-sources';
import { CLASSIFICATION_OPTIONS } from '@/lib/constants';
import { DocumentClassification, SyncStatus, UserRole } from '@/lib/types';
import { cn } from '@/lib/utils';
import type { LucideIcon } from 'lucide-react';

interface TileProps {
  label: string;
  value: number | string;
  icon: LucideIcon;
  accent: string;
  hint?: string;
}

function StatTile({ label, value, icon: Icon, accent, hint }: TileProps) {
  return (
    <Card>
      <CardContent className="flex items-center gap-4 p-5">
        <span
          className={cn(
            'flex h-11 w-11 shrink-0 items-center justify-center rounded-xl',
            accent,
          )}
        >
          <Icon className="h-5 w-5" />
        </span>
        <div className="min-w-0">
          <p className="text-2xl font-semibold tabular-nums tracking-tight text-foreground">
            {value}
          </p>
          <p className="truncate text-sm text-muted-foreground">{label}</p>
          {hint && (
            <p className="truncate text-xs text-muted-foreground/80">{hint}</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function AdminOverviewInner() {
  // Pull a generous page so counts/distributions reflect the whole catalog in
  // typical installations; totals themselves come from the paginator.
  const docs = useDocuments(1, 100);
  const sources = useKnowledgeSources(1, 100);

  const loading = docs.isLoading || sources.isLoading;

  const docItems = docs.data?.items ?? [];
  const sourceItems = sources.data?.items ?? [];
  const totalDocs = docs.data?.pagination.total_items ?? 0;
  const totalSources = sources.data?.pagination.total_items ?? 0;
  const activeSources = sourceItems.filter((s) => s.is_active).length;
  const failedSources = sourceItems.filter(
    (s) => s.sync_status === SyncStatus.FAILED,
  ).length;

  // Sampled distributions (based on the loaded page).
  const sampleCount = docItems.length;
  const classCounts = CLASSIFICATION_OPTIONS.map((c) => ({
    classification: c as DocumentClassification,
    count: docItems.filter((d) => d.classification === c).length,
  })).filter((row) => row.count > 0);
  const maxClass = Math.max(1, ...classCounts.map((r) => r.count));

  const statusCounts = Object.values(SyncStatus)
    .map((status) => ({
      status: status as SyncStatus,
      count: sourceItems.filter((s) => s.sync_status === status).length,
    }))
    .filter((row) => row.count > 0);

  const sampled = sampleCount < totalDocs;

  if (loading) {
    return (
      <div className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
        <Skeleton className="h-8 w-48" />
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-24 w-full rounded-2xl" />
          ))}
        </div>
        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          <Skeleton className="h-64 w-full rounded-2xl" />
          <Skeleton className="h-64 w-full rounded-2xl" />
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          Overview
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          A snapshot of the knowledge base and its connectors.
        </p>
      </div>

      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile
          label="Documents"
          value={totalDocs.toLocaleString()}
          icon={FileText}
          accent="bg-sky-500/10 text-sky-600 dark:text-sky-300"
        />
        <StatTile
          label="Knowledge sources"
          value={totalSources.toLocaleString()}
          icon={Library}
          accent="bg-indigo-500/10 text-indigo-600 dark:text-indigo-300"
        />
        <StatTile
          label="Active sources"
          value={activeSources.toLocaleString()}
          hint={
            totalSources > 0 ? `${totalSources - activeSources} inactive` : undefined
          }
          icon={CheckCircle2}
          accent="bg-emerald-500/10 text-emerald-600 dark:text-emerald-300"
        />
        <StatTile
          label="Failed syncs"
          value={failedSources.toLocaleString()}
          icon={AlertTriangle}
          accent={cn(
            failedSources > 0
              ? 'bg-rose-500/10 text-rose-600 dark:text-rose-300'
              : 'bg-muted text-muted-foreground',
          )}
        />
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Documents by access level</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {classCounts.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">
                No documents to summarize yet.
              </p>
            ) : (
              <>
                {classCounts.map((row) => (
                  <div key={row.classification} className="space-y-1.5">
                    <div className="flex items-center justify-between gap-3">
                      <ClassificationBadge classification={row.classification} />
                      <span className="text-sm font-medium tabular-nums text-foreground">
                        {row.count}
                      </span>
                    </div>
                    <div
                      className="h-2 overflow-hidden rounded-full bg-muted"
                      role="img"
                      aria-label={`${row.count} ${row.classification} documents`}
                    >
                      <div
                        className="h-full rounded-full bg-primary"
                        style={{
                          width: `${Math.round((row.count / maxClass) * 100)}%`,
                        }}
                      />
                    </div>
                  </div>
                ))}
                {sampled && (
                  <p className="pt-1 text-xs text-muted-foreground">
                    Distribution based on the {sampleCount} most recent of{' '}
                    {totalDocs} documents.
                  </p>
                )}
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Source sync status</CardTitle>
          </CardHeader>
          <CardContent>
            {statusCounts.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">
                No knowledge sources yet.
              </p>
            ) : (
              <ul className="divide-y divide-border">
                {statusCounts.map((row) => (
                  <li
                    key={row.status}
                    className="flex items-center justify-between py-2.5"
                  >
                    <SyncStatusBadge status={row.status} />
                    <span className="text-sm font-medium tabular-nums text-foreground">
                      {row.count}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default function AdminOverviewPage() {
  return (
    <RoleGuard roles={[UserRole.ADMIN]}>
      <AdminOverviewInner />
    </RoleGuard>
  );
}
