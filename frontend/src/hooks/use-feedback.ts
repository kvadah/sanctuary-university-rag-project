'use client';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { chatApi } from '@/lib/api';
import { FeedbackRequest } from '@/lib/types';
import { conversationKeys } from './use-conversations';

export function useSubmitFeedback(conversationId?: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: FeedbackRequest) => chatApi.feedback(body),
    onSuccess: () => {
      if (conversationId) {
        queryClient.invalidateQueries({
          queryKey: conversationKeys.detail(conversationId),
        });
      }
    },
  });
}
