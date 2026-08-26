'use client';

import {
  Boxes,
  Coins,
  FileText,
  Library,
  MessageSquare,
  Timer,
  ThumbsUp,
  Users,
} from 'lucide-react';
import { StatTile } from '@/components/admin/stat-tile';
import { RoleGuard } from '@/components/layout/role-guard';
import { IndexingStatusBadge } from '@/components/documents/indexing-status-badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { EmptyState } from '@/components/ui/empty-state';
import { useAnalytics } from '@/hooks/use-analytics';
import { IndexingStatus, UserRole } from '@/lib/types';

// --- small formatters (kept local; display-only) ----------------------------

function formatMs(ms: number | null): string {
  if (ms === null) return '—';
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${Math.round(ms)} ms`;
}

function formatPct(ratio: number | null): string {
  return ratio === null ? '—' : `${Math.round(ratio * 100)}%`;
}

// TZ-safe short label from an ISO "YYYY-MM-DD" (avoid Date parsing quirks).
function shortDay(iso: string): string {
  const [, m, d] = iso.split('-');
  return `${Number(m)}/${Number(d)}`;
}

function AnalyticsInner() {
  const { data, isLoading, isError } = useAnalytics(30);

  if (isLoading) {
    return (
      <div className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
        <Skeleton className="h-8 w-40" />
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-24 w-full rounded-2xl" />
          ))}
        </div>
        <Skeleton className="mt-6 h-64 w-full rounded-2xl" />
        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          <Skeleton className="h-56 w-full rounded-2xl" />
          <Skeleton className="h-56 w-full rounded-2xl" />
        </div>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="mx-auto w-full max-w-3xl p-6 lg:p-8">
        <EmptyState
          icon={Timer}
          title="Couldn't load analytics"
          description="The metrics service didn't respond. Please try again in a moment."
        />
      </div>
    );
  }

  const { usage, latency_ms, tokens, quality, content, indexing } = data;

  const volumeMax = Math.max(1, ...usage.volume_by_day.map((p) => p.count));
  const hasVolume = usage.volume_by_day.some((p) => p.count > 0);

  // Latency bars are scaled against p95 (the tallest of the three).
  const latencyBase = Math.max(
    latency_ms.p95 ?? 0,
    latency_ms.avg ?? 0,
    latency_ms.p50 ?? 0,
    1,
  );
  const latencyRows: { label: string; value: number | null }[] = [
    { label: 'Average', value: latency_ms.avg },
    { label: 'Median (p50)', value: latency_ms.p50 },
    { label: '95th pct (p95)', value: latency_ms.p95 },
  ];

  const jobStatuses = Object.entries(indexing.by_status);

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          Analytics
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Usage, performance, and answer quality over the last {data.window_days}{' '}
          days.
        </p>
      </div>

      {/* Headline metrics */}
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile
          label="Questions asked"
          value={usage.total_queries.toLocaleString()}
          hint={`${usage.conversations.toLocaleString()} conversation${
            usage.conversations === 1 ? '' : 's'
          }`}
          icon={MessageSquare}
          accent="bg-sky-500/10 text-sky-600 dark:text-sky-300"
        />
        <StatTile
          label="Avg. answer time"
          value={formatMs(latency_ms.avg)}
          hint={
            latency_ms.p95 !== null ? `p95 ${formatMs(latency_ms.p95)}` : undefined
          }
          icon={Timer}
          accent="bg-amber-500/10 text-amber-600 dark:text-amber-300"
        />
        <StatTile
          label="Tokens used"
          value={tokens.total.toLocaleString()}
          hint={`${tokens.prompt.toLocaleString()} in · ${tokens.completion.toLocaleString()} out`}
          icon={Coins}
          accent="bg-violet-500/10 text-violet-600 dark:text-violet-300"
        />
        <StatTile
          label="Satisfaction"
          value={formatPct(quality.up_ratio)}
          hint={`${quality.feedback_total.toLocaleString()} rating${
            quality.feedback_total === 1 ? '' : 's'
          }`}
          icon={ThumbsUp}
          accent="bg-emerald-500/10 text-emerald-600 dark:text-emerald-300"
        />
      </div>

      {/* Query volume over time */}
      <div className="mt-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Questions per day</CardTitle>
          </CardHeader>
          <CardContent>
            {!hasVolume ? (
              <p className="py-10 text-center text-sm text-muted-foreground">
                No questions asked in this window yet.
              </p>
            ) : (
              <>
                <div className="flex h-40 items-end gap-1">
                  {usage.volume_by_day.map((p) => (
                    <div
                      key={p.date}
                      className="group flex h-full flex-1 items-end"
                      title={`${p.date}: ${p.count}`}
                    >
                      <div
                        className="w-full rounded-t bg-primary/80 transition-colors group-hover:bg-primary"
                        style={{
                          height: `${Math.round((p.count / volumeMax) * 100)}%`,
                        }}
                      />
                    </div>
                  ))}
                </div>
                <div className="mt-2 flex justify-between text-xs text-muted-foreground">
                  <span>{shortDay(usage.volume_by_day[0].date)}</span>
                  <span>
                    Peak {volumeMax} / day
                  </span>
                  <span>
                    {shortDay(
                      usage.volume_by_day[usage.volume_by_day.length - 1].date,
                    )}
                  </span>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        {/* Latency breakdown */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Answer latency</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {latency_ms.sample_count === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">
                No latency recorded yet.
              </p>
            ) : (
              <>
                {latencyRows.map((row) => (
                  <div key={row.label} className="space-y-1.5">
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-sm text-muted-foreground">
                        {row.label}
                      </span>
                      <span className="text-sm font-medium tabular-nums text-foreground">
                        {formatMs(row.value)}
                      </span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full rounded-full bg-amber-500"
                        style={{
                          width: `${Math.round(
                            ((row.value ?? 0) / latencyBase) * 100,
                          )}%`,
                        }}
                      />
                    </div>
                  </div>
                ))}
                <p className="pt-1 text-xs text-muted-foreground">
                  Based on {latency_ms.sample_count.toLocaleString()} answered
                  question{latency_ms.sample_count === 1 ? '' : 's'}.
                </p>
              </>
            )}
          </CardContent>
        </Card>

        {/* Answer quality */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Answer quality</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <div className="flex items-center justify-between gap-3">
                <span className="text-sm text-muted-foreground">
                  Positive feedback
                </span>
                <span className="text-sm font-medium tabular-nums text-foreground">
                  {formatPct(quality.up_ratio)}
                </span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-emerald-500"
                  style={{ width: `${Math.round((quality.up_ratio ?? 0) * 100)}%` }}
                />
              </div>
              <p className="text-xs text-muted-foreground">
                {quality.feedback_up.toLocaleString()} up ·{' '}
                {quality.feedback_down.toLocaleString()} down ·{' '}
                {quality.feedback_total.toLocaleString()} total
              </p>
            </div>

            <div className="border-t border-border pt-3">
              <div className="flex items-center justify-between gap-3">
                <span className="text-sm text-muted-foreground">
                  “No information” answers
                </span>
                <span className="text-sm font-medium tabular-nums text-foreground">
                  {formatPct(quality.refusal_rate)}
                </span>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                {quality.refusal_count.toLocaleString()} answer
                {quality.refusal_count === 1 ? '' : 's'} where no matching documents
                were found.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Content inventory */}
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile
          label="Documents"
          value={content.documents.toLocaleString()}
          icon={FileText}
          accent="bg-sky-500/10 text-sky-600 dark:text-sky-300"
        />
        <StatTile
          label="Indexed chunks"
          value={content.chunks.toLocaleString()}
          icon={Boxes}
          accent="bg-indigo-500/10 text-indigo-600 dark:text-indigo-300"
        />
        <StatTile
          label="Knowledge sources"
          value={content.sources.toLocaleString()}
          hint={`${content.active_sources.toLocaleString()} active`}
          icon={Library}
          accent="bg-emerald-500/10 text-emerald-600 dark:text-emerald-300"
        />
        <StatTile
          label="Users"
          value={content.users.toLocaleString()}
          icon={Users}
          accent="bg-slate-500/10 text-slate-600 dark:text-slate-300"
        />
      </div>

      {/* Indexing jobs */}
      <div className="mt-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              Indexing jobs ({indexing.total.toLocaleString()})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {jobStatuses.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">
                No indexing jobs yet.
              </p>
            ) : (
              <ul className="divide-y divide-border">
                {jobStatuses.map(([status, count]) => (
                  <li
                    key={status}
                    className="flex items-center justify-between py-2.5"
                  >
                    <IndexingStatusBadge status={status as IndexingStatus} />
                    <span className="text-sm font-medium tabular-nums text-foreground">
                      {count.toLocaleString()}
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

export default function AnalyticsPage() {
  return (
    <RoleGuard roles={[UserRole.ADMIN]}>
      <AnalyticsInner />
    </RoleGuard>
  );
}
