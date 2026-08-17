import { SyncStatus } from '@/lib/types';
import { SYNC_STATUS_META } from '@/lib/constants';
import { cn } from '@/lib/utils';

export function SyncStatusBadge({
  status,
  className,
}: {
  status: SyncStatus;
  className?: string;
}) {
  const meta = SYNC_STATUS_META[status];
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 text-xs font-medium',
        meta.className,
        className,
      )}
    >
      <span className={cn('h-1.5 w-1.5 rounded-full', meta.dot)} />
      {meta.label}
    </span>
  );
}
