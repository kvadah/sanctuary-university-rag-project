'use client';

import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '@/lib/api';

export const analyticsKeys = {
  all: ['analytics'] as const,
  overview: (days: number) => ['analytics', 'overview', days] as const,
};

/** Admin analytics overview for the given window (default 30 days). */
export function useAnalytics(days = 30) {
  return useQuery({
    queryKey: analyticsKeys.overview(days),
    queryFn: () => analyticsApi.overview(days),
  });
}
