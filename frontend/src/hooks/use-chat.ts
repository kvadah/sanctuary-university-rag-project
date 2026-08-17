'use client';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { chatApi } from '@/lib/api';
import { ChatQueryRequest } from '@/lib/types';
import { conversationKeys } from './use-conversations';

/**
 * Send a chat query. On success, refresh the conversation list (title/order may
 * change) and the active conversation's message history.
 */
export function useSendMessage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: ChatQueryRequest) => chatApi.query(body),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: conversationKeys.all });
      queryClient.invalidateQueries({
        queryKey: conversationKeys.detail(data.conversation_id),
      });
    },
  });
}
