'use client';

import Link from 'next/link';
import { ShieldAlert } from 'lucide-react';
import { useAuthStore } from '@/stores/auth-store';
import { UserRole } from '@/lib/types';
import { Spinner } from '@/components/ui/spinner';
import { EmptyState } from '@/components/ui/empty-state';
import { Button } from '@/components/ui/button';

/**
 * Renders children only for users whose role is in `roles`. Assumes it lives
 * inside an AuthGuard (a user is present after hydration). Shows a friendly
 * "not authorized" panel rather than redirecting, to avoid flicker.
 */
export function RoleGuard({
  roles,
  children,
}: {
  roles: UserRole[];
  children: React.ReactNode;
}) {
  const user = useAuthStore((s) => s.user);
  const hasHydrated = useAuthStore((s) => s.hasHydrated);

  if (!hasHydrated || !user) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner className="h-6 w-6" />
      </div>
    );
  }

  if (!roles.includes(user.role)) {
    return (
      <div className="mx-auto w-full max-w-3xl p-6 lg:p-8">
        <EmptyState
          icon={ShieldAlert}
          title="Not authorized"
          description="You don't have permission to view this page."
          action={
            <Link href="/chat">
              <Button>Back to Assistant</Button>
            </Link>
          }
        />
      </div>
    );
  }

  return <>{children}</>;
}
