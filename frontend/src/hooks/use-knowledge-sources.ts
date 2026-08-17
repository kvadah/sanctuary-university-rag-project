'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { knowledgeApi } from '@/lib/api';
import { KnowledgeSourceCreate, KnowledgeSourceUpdate } from '@/lib/types';

export const knowledgeKeys = {
  all: ['knowledge-sources'] as const,
  list: (page: number, pageSize: number) =>
    ['knowledge-sources', 'list', page, pageSize] as const,
  detail: (id: string) => ['knowledge-sources', 'detail', id] as const,
};

export function useKnowledgeSources(page = 1, pageSize = 50) {
  return useQuery({
    queryKey: knowledgeKeys.list(page, pageSize),
    queryFn: () => knowledgeApi.list(page, pageSize),
  });
}

export function useCreateSource() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: KnowledgeSourceCreate) => knowledgeApi.create(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: knowledgeKeys.all });
    },
  });
}

export function useUpdateSource() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: KnowledgeSourceUpdate }) =>
      knowledgeApi.update(id, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: knowledgeKeys.all });
    },
  });
}

export function useDeleteSource() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => knowledgeApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: knowledgeKeys.all });
    },
  });
}
