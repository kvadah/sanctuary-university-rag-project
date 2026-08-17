'use client';

import { useRouter } from 'next/navigation';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { authApi } from '@/lib/api';
import { useAuthStore } from '@/stores/auth-store';
import { LoginRequest, RegisterRequest } from '@/lib/types';

/**
 * Log in, persist the token, then fetch the profile before redirecting.
 * The axios request interceptor reads the token from the store synchronously,
 * so `me()` below is already authenticated.
 */
export function useLogin() {
  const router = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);
  const setUser = useAuthStore((s) => s.setUser);

  return useMutation({
    mutationFn: async (body: LoginRequest) => {
      const token = await authApi.login(body);
      setAuth(token);
      const user = await authApi.me();
      setUser(user);
      return user;
    },
    onSuccess: () => {
      router.push('/chat');
    },
  });
}

/** Register, then immediately log the new user in and redirect. */
export function useRegister() {
  const router = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);
  const setUser = useAuthStore((s) => s.setUser);

  return useMutation({
    mutationFn: async (body: RegisterRequest) => {
      await authApi.register(body);
      const token = await authApi.login({
        email: body.email,
        password: body.password,
      });
      setAuth(token);
      const user = await authApi.me();
      setUser(user);
      return user;
    },
    onSuccess: () => {
      router.push('/chat');
    },
  });
}

/** Returns a stable logout callback that clears auth + cached queries. */
export function useLogout() {
  const router = useRouter();
  const logout = useAuthStore((s) => s.logout);
  const queryClient = useQueryClient();

  return () => {
    logout();
    queryClient.clear();
    router.push('/login');
  };
}
