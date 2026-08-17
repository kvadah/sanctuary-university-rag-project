import { DocumentClassification } from '@/lib/types';
import { classificationMeta } from '@/lib/utils';
import { cn } from '@/lib/utils';

export function ClassificationBadge({
  classification,
  className,
}: {
  classification: DocumentClassification;
  className?: string;
}) {
  const meta = classificationMeta(classification);
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset',
        meta.className,
        className,
      )}
    >
      {meta.label}
    </span>
  );
}
