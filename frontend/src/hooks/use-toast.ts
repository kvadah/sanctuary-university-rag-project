import { create } from 'zustand';

export type ToastVariant = 'default' | 'success' | 'error' | 'info';

export interface Toast {
  id: string;
  title?: string;
  description?: string;
  variant: ToastVariant;
}

interface ToastState {
  toasts: Toast[];
  push: (toast: Omit<Toast, 'id' | 'variant'> & { id?: string; variant?: ToastVariant }) => string;
  dismiss: (id: string) => void;
}

// Module-level counter (not Math.random) so ids are stable and SSR-safe.
let counter = 0;
function nextId(): string {
  counter += 1;
  return `toast-${counter}`;
}

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],
  push: (toast) => {
    const id = toast.id ?? nextId();
    set((state) => ({
      toasts: [...state.toasts, { variant: 'default', ...toast, id }],
    }));
    return id;
  },
  dismiss: (id) =>
    set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) })),
}));

export function useToast() {
  const push = useToastStore((s) => s.push);
  const dismiss = useToastStore((s) => s.dismiss);
  return {
    toast: push,
    success: (title: string, description?: string) =>
      push({ title, description, variant: 'success' }),
    error: (title: string, description?: string) =>
      push({ title, description, variant: 'error' }),
    info: (title: string, description?: string) =>
      push({ title, description, variant: 'info' }),
    dismiss,
  };
}
