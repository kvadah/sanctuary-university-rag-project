'use client';

import type { LucideIcon } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

export interface StatTileProps {
  label: string;
  value: number | string;
  icon: LucideIcon;
  accent: string;
  hint?: string;
}

/**
 * Compact metric tile: an accented icon beside a big value with a label and
 * optional hint. Shared by the admin Overview and Analytics pages.
 */
export function StatTile({ label, value, icon: Icon, accent, hint }: StatTileProps) {
  return (
    <Card>
      <CardContent className="flex items-center gap-4 p-5">
        <span
          className={cn(
            'flex h-11 w-11 shrink-0 items-center justify-center rounded-xl',
            accent,
          )}
        >
          <Icon className="h-5 w-5" />
        </span>
        <div className="min-w-0">
          <p className="text-2xl font-semibold tabular-nums tracking-tight text-foreground">
            {value}
          </p>
          <p className="truncate text-sm text-muted-foreground">{label}</p>
          {hint && (
            <p className="truncate text-xs text-muted-foreground/80">{hint}</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
