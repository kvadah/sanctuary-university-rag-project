import Link from 'next/link';
import { Sparkles } from 'lucide-react';

interface AuthCardProps {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
}

export function AuthCard({ title, subtitle, children, footer }: AuthCardProps) {
  return (
    <div className="w-full max-w-md">
      <div className="mb-6 flex flex-col items-center text-center">
        <Link href="/" className="mb-4">
          <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-tr from-sky-600 to-indigo-600 text-white shadow-md">
            <Sparkles className="h-6 w-6" />
          </span>
        </Link>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">
          {title}
        </h1>
        {subtitle && (
          <p className="mt-1.5 text-sm text-muted-foreground">{subtitle}</p>
        )}
      </div>

      <div className="rounded-2xl border bg-card p-6 shadow-sm sm:p-8">
        {children}
      </div>

      {footer && (
        <p className="mt-6 text-center text-sm text-muted-foreground">{footer}</p>
      )}
    </div>
  );
}
