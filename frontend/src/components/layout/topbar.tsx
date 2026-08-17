'use client';

import { Menu } from 'lucide-react';
import { usePathname } from 'next/navigation';
import { NAV_ITEMS } from '@/lib/constants';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { UserMenu } from './user-menu';

function currentTitle(pathname: string): string {
  const exact = NAV_ITEMS.find((i) => i.href === pathname);
  if (exact) return exact.label;
  const prefix = NAV_ITEMS.filter((i) => pathname.startsWith(`${i.href}/`)).sort(
    (a, b) => b.href.length - a.href.length,
  )[0];
  return prefix?.label ?? '';
}

export function Topbar({ onMenuClick }: { onMenuClick: () => void }) {
  const pathname = usePathname();
  const title = currentTitle(pathname);

  return (
    <header className="flex h-16 shrink-0 items-center gap-3 border-b bg-card/80 px-4 backdrop-blur lg:px-6">
      <button
        type="button"
        onClick={onMenuClick}
        aria-label="Open navigation"
        className="inline-flex h-10 w-10 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring lg:hidden"
      >
        <Menu className="h-5 w-5" />
      </button>
      <h1 className="truncate text-base font-semibold text-foreground">
        {title}
      </h1>
      <div className="ml-auto flex items-center gap-1 sm:gap-2">
        <ThemeToggle />
        <UserMenu />
      </div>
    </header>
  );
}
