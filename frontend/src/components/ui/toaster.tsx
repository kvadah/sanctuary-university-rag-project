'use client';

import { useEffect } from 'react';
import { CheckCircle2, Info, X, XCircle } from 'lucide-react';
import { Toast, ToastVariant, useToastStore } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';

const ICONS: Record<ToastVariant, typeof Info> = {
  success: CheckCircle2,
  error: XCircle,
  info: Info,
  default: Info,
};

const ACCENT: Record<ToastVariant, string> = {
  success: 'border-l-4 border-l-emerald-500',
  error: 'border-l-4 border-l-rose-500',
  info: 'border-l-4 border-l-sky-500',
  default: 'border-l-4 border-l-slate-400',
};

const ICON_COLOR: Record<ToastVariant, string> = {
  success: 'text-emerald-500',
  error: 'text-rose-500',
  info: 'text-sky-500',
  default: 'text-slate-400',
};

function ToastCard({ toast }: { toast: Toast }) {
  const dismiss = useToastStore((s) => s.dismiss);

  useEffect(() => {
    const timer = setTimeout(() => dismiss(toast.id), 4500);
    return () => clearTimeout(timer);
  }, [toast.id, dismiss]);

  const Icon = ICONS[toast.variant];

  return (
    <div
      role="status"
      className={cn(
        'pointer-events-auto flex w-80 items-start gap-3 rounded-xl border bg-card p-4 shadow-lg animate-slide-up',
        ACCENT[toast.variant],
      )}
    >
      <Icon className={cn('mt-0.5 h-5 w-5 shrink-0', ICON_COLOR[toast.variant])} />
      <div className="flex-1 text-sm">
        {toast.title && (
          <p className="font-semibold text-card-foreground">{toast.title}</p>
        )}
        {toast.description && (
          <p className="mt-0.5 text-muted-foreground">{toast.description}</p>
        )}
      </div>
      <button
        type="button"
        onClick={() => dismiss(toast.id)}
        className="text-muted-foreground transition-colors hover:text-foreground"
        aria-label="Dismiss notification"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}

export function Toaster() {
  const toasts = useToastStore((s) => s.toasts);
  return (
    <div className="pointer-events-none fixed bottom-4 right-4 z-[100] flex flex-col gap-2">
      {toasts.map((toast) => (
        <ToastCard key={toast.id} toast={toast} />
      ))}
    </div>
  );
}
