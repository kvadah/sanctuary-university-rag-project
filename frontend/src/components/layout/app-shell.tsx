'use client';

import { useState } from 'react';
import { Sidebar } from './sidebar';
import { Topbar } from './topbar';
import { usePersistentBoolean } from '@/hooks/use-persistent-boolean';

export function AppShell({ children }: { children: React.ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  // Left navigation sidebar collapses on desktop; collapsed by default. The
  // choice is persisted so it survives reloads and page navigation.
  const [navCollapsed, setNavCollapsed] = usePersistentBoolean(
    'nav-collapsed',
    true,
  );

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Desktop sidebar — hidden while collapsed */}
      {!navCollapsed && (
        <aside className="hidden w-64 shrink-0 border-r bg-card lg:block">
          <Sidebar />
        </aside>
      )}

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="absolute inset-0 animate-fade-in bg-slate-950/50"
            onClick={() => setMobileOpen(false)}
          />
          <aside className="absolute inset-y-0 left-0 w-64 animate-fade-in border-r bg-card shadow-xl">
            <Sidebar onNavigate={() => setMobileOpen(false)} />
          </aside>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar
          onMenuClick={() => setMobileOpen(true)}
          onToggleNav={() => setNavCollapsed((c) => !c)}
          navCollapsed={navCollapsed}
        />
        <main className="min-h-0 flex-1 overflow-y-auto scrollbar-thin">
          {children}
        </main>
      </div>
    </div>
  );
}
