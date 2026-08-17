'use client';

import { AuthGuard } from '@/components/layout/auth-guard';
import { AppShell } from '@/components/layout/app-shell';

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthGuard>
      <AppShell>{children}</AppShell>
    </AuthGuard>
  );
}
