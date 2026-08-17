'use client';

import { Trash2, AlertTriangle } from 'lucide-react';
import { Dialog } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { useDeleteSource } from '@/hooks/use-knowledge-sources';
import { useToast } from '@/hooks/use-toast';
import { KnowledgeSource } from '@/lib/types';
import { extractError } from '@/lib/utils';

interface DeleteConfirmDialogProps {
  source: KnowledgeSource | null;
  onClose: () => void;
}

export function DeleteConfirmDialog({
  source,
  onClose,
}: DeleteConfirmDialogProps) {
  const remove = useDeleteSource();
  const { success, error: toastError } = useToast();

  const confirm = () => {
    if (!source) return;
    remove.mutate(source.id, {
      onSuccess: () => {
        success('Source deleted', `“${source.name}” was removed.`);
        onClose();
      },
      onError: (err) => toastError('Delete failed', extractError(err)),
    });
  };

  return (
    <Dialog
      open={Boolean(source)}
      onClose={() => {
        if (!remove.isPending) onClose();
      }}
      title="Delete knowledge source"
      className="max-w-md"
      footer={
        <>
          <Button
            variant="outline"
            onClick={onClose}
            disabled={remove.isPending}
          >
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={confirm}
            loading={remove.isPending}
          >
            <Trash2 className="h-4 w-4" />
            Delete
          </Button>
        </>
      }
    >
      <div className="flex items-start gap-3">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-destructive/10 text-destructive">
          <AlertTriangle className="h-5 w-5" />
        </span>
        <p className="text-sm text-muted-foreground">
          Are you sure you want to delete{' '}
          <span className="font-medium text-foreground">{source?.name}</span>?
          This removes the source and its associated documents from the catalog.
          This action can’t be undone.
        </p>
      </div>
    </Dialog>
  );
}
