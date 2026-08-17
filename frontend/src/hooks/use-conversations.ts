'use client';

import { useQuery } from '@tanstack/react-query';
import { chatApi } from '@/lib/api';

export const conversationKeys = {
  all: ['conversations'] as const,
  list: (page: number) => ['conversations', 'list', page] as const,
  detail: (id: string) => ['conversations', 'detail', id] as const,
};

export function useConversations(page = 1, pageSize = 50) {
  return useQuery({
    queryKey: conversationKeys.list(page),
    queryFn: () => chatApi.listConversations(page, pageSize),
  });
}

export function useConversation(id: string | null) {
  return useQuery({
    queryKey: conversationKeys.detail(id ?? 'none'),
    queryFn: () => chatApi.getConversation(id as string),
    enabled: Boolean(id),
  });
}
