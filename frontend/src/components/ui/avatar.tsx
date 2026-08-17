import { cn, initials } from '@/lib/utils';

interface AvatarProps {
  first?: string;
  last?: string;
  className?: string;
}

export function Avatar({ first, last, className }: AvatarProps) {
  return (
    <span
      className={cn(
        'inline-flex h-9 w-9 select-none items-center justify-center rounded-full bg-gradient-to-tr from-sky-600 to-indigo-600 text-sm font-semibold text-white',
        className,
      )}
    >
      {initials(first, last)}
    </span>
  );
}
