'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { documentsApi, UploadParams } from '@/lib/api';

export const documentKeys = {
  all: ['documents'] as const,
  list: (page: number, pageSize: number) =>
    ['documents', 'list', page, pageSize] as const,
};

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
      queryClient.invalidateQueries({ queryKey: documentKeys.all });
    },
  });
}
