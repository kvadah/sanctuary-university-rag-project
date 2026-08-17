import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';
import { AuthToken, User } from '@/lib/types';

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  user: User | null;
  /** True once the persisted store has rehydrated from localStorage. */
  hasHydrated: boolean;
  setAuth: (token: AuthToken) => void;
  setUser: (user: User | null) => void;
  logout: () => void;
  setHasHydrated: (value: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      refreshToken: null,
      user: null,
      hasHydrated: false,
      setAuth: (token) =>
        set({
          token: token.access_token,
          refreshToken: token.refresh_token,
        }),
      setUser: (user) => set({ user }),
      logout: () => set({ token: null, refreshToken: null, user: null }),
      setHasHydrated: (value) => set({ hasHydrated: value }),
    }),
    {
      name: 'kh-auth',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        token: state.token,
        refreshToken: state.refreshToken,
        user: state.user,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
      },
    },
  ),
);
