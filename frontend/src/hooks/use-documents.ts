'use client';

import { useEffect, useRef } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { documentsApi, UploadParams } from '@/lib/api';
import { IndexingJob, IndexingStatus } from '@/lib/types';

export const documentKeys = {
  all: ['documents'] as const,
  list: (page: number, pageSize: number) =>
    ['documents', 'list', page, pageSize] as const,
};

export const indexingJobKeys = {
  all: ['indexing-jobs'] as const,
  list: (limit: number) => ['indexing-jobs', 'list', limit] as const,
};

const ACTIVE_STATUSES: IndexingStatus[] = [
  IndexingStatus.PENDING,
  IndexingStatus.PROCESSING,
];

export function isActiveJob(job: IndexingJob): boolean {
  return ACTIVE_STATUSES.includes(job.status);
}

function hasActiveJobs(jobs?: IndexingJob[]): boolean {
  return !!jobs?.some(isActiveJob);
}

export function useDocuments(page = 1, pageSize = 20) {
  return useQuery({
    queryKey: documentKeys.list(page, pageSize),
    queryFn: () => documentsApi.list(page, pageSize),
  });
}

export function useUploadDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params: UploadParams) => documentsApi.upload(params),
    onSuccess: () => {
      // Show the freshly-queued job right away; the finished document arrives
      // later via useIndexingJobs' completion invalidation.
      queryClient.invalidateQueries({ queryKey: indexingJobKeys.all });
    },
  });
}

/**
 * Poll recent indexing jobs while any are in flight (every 2s), and refresh the
 * documents list once a job leaves the active set so the finished document
 * appears. Pass `enabled=false` for users who can't upload (no jobs to watch).
 */
export function useIndexingJobs(enabled = true, limit = 20) {
  const queryClient = useQueryClient();
  const prevActiveIds = useRef<Set<string>>(new Set());

  const query = useQuery({
    queryKey: indexingJobKeys.list(limit),
    queryFn: () => documentsApi.listJobs(limit),
    enabled,
    refetchInterval: (q) => (hasActiveJobs(q.state.data) ? 2000 : false),
  });

  useEffect(() => {
    const jobs = query.data ?? [];
    const activeIds = new Set(jobs.filter(isActiveJob).map((j) => j.id));
    // Any id active last tick but not now means a job just settled.
    let settled = false;
    prevActiveIds.current.forEach((id) => {
      if (!activeIds.has(id)) settled = true;
    });
    if (settled) {
      queryClient.invalidateQueries({ queryKey: documentKeys.all });
    }
    prevActiveIds.current = activeIds;
  }, [query.data, queryClient]);

  return query;
}
