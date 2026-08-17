'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Sparkles } from 'lucide-react';
import { APP_NAME, APP_SUBTITLE, NAV_ITEMS } from '@/lib/constants';
import { useAuthStore } from '@/stores/auth-store';
import { cn } from '@/lib/utils';

function isActive(pathname: string, href: string): boolean {
  // "/admin" (Overview) must not stay active on nested admin routes.
  if (href === '/admin') return pathname === href;
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const user = useAuthStore((s) => s.user);

  const items = NAV_ITEMS.filter(
    (item) => !item.roles || (user && item.roles.includes(user.role)),
  );

  return (
    <div className="flex h-full flex-col">
      <Link
        href="/chat"
        onClick={onNavigate}
        className="flex items-center gap-3 border-b px-5 py-5"
      >
        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-sky-600 to-indigo-600 text-white shadow-sm">
          <Sparkles className="h-5 w-5" />
        </span>
        <span className="min-w-0">
          <span className="block truncate text-sm font-semibold leading-tight text-foreground">
            {APP_NAME}
          </span>
          <span className="block truncate text-xs text-muted-foreground">
            {APP_SUBTITLE}
          </span>
        </span>
      </Link>

      <nav className="flex-1 space-y-1 overflow-y-auto p-3 scrollbar-thin">
        {items.map((item) => {
          const active = isActive(pathname, item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                active
                  ? 'bg-primary/10 text-primary'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground',
              )}
            >
              <Icon className="h-[18px] w-[18px] shrink-0" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t p-4">
        <p className="text-xs text-muted-foreground">
          Answers are AI-generated from institutional documents. Verify against
          official sources.
        </p>
      </div>
    </div>
  );
}
