'use client';

import { Monitor, Moon, Sun } from 'lucide-react';
import { useTheme } from '@/providers/theme-provider';
import { Theme } from '@/lib/types';
import { cn } from '@/lib/utils';

const ORDER: Theme[] = ['light', 'dark', 'system'];
const ICONS: Record<Theme, typeof Sun> = {
  light: Sun,
  dark: Moon,
  system: Monitor,
};
const LABELS: Record<Theme, string> = {
  light: 'Light',
  dark: 'Dark',
  system: 'System',
};

/** Compact icon button that cycles light → dark → system. */
export function ThemeToggle({ className }: { className?: string }) {
  const { theme, setTheme } = useTheme();
  const Icon = ICONS[theme];
  const next = ORDER[(ORDER.indexOf(theme) + 1) % ORDER.length];
  return (
    <button
      type="button"
      onClick={() => setTheme(next)}
      title={`Theme: ${LABELS[theme]} — click for ${LABELS[next]}`}
      aria-label={`Switch theme (current: ${LABELS[theme]})`}
      className={cn(
        'inline-flex h-10 w-10 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
        className,
      )}
    >
      <Icon className="h-5 w-5" />
    </button>
  );
}

/** Full three-way segmented control for the settings page. */
export function ThemeSegmented() {
  const { theme, setTheme } = useTheme();
  return (
    <div className="inline-flex rounded-lg border border-input bg-card p-1">
      {ORDER.map((t) => {
        const Icon = ICONS[t];
        const active = theme === t;
        return (
          <button
            key={t}
            type="button"
            onClick={() => setTheme(t)}
            className={cn(
              'inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
              active
                ? 'bg-primary text-primary-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground',
            )}
          >
            <Icon className="h-4 w-4" />
            {LABELS[t]}
          </button>
        );
      })}
    </div>
  );
}
