'use client';

import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { authApi } from '@/lib/api';
import { useAuthStore } from '@/stores/auth-store';

/**
 * Validates the persisted session on load: if a token exists, fetch /me to
 * refresh the user record; on failure, clear the session. Does not gate
 * rendering — route protection is handled by AuthGuard/RoleGuard.
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token);
  const hasHydrated = useAuthStore((s) => s.hasHydrated);
  const setUser = useAuthStore((s) => s.setUser);
  const logout = useAuthStore((s) => s.logout);

  const { data, isError } = useQuery({
    queryKey: ['me', token],
    queryFn: authApi.me,
    enabled: hasHydrated && !!token,
    retry: false,
    staleTime: 5 * 60_000,
  });

  useEffect(() => {
    if (data) setUser(data);
  }, [data, setUser]);

  useEffect(() => {
    if (isError) logout();
  }, [isError, logout]);

  return <>{children}</>;
}
