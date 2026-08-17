'use client';

import Link from 'next/link';
import {
  BookOpen,
  Search,
  ShieldCheck,
  Sparkles,
  UserCheck,
  Cpu,
  ArrowRight,
} from 'lucide-react';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { useAuthStore } from '@/stores/auth-store';
import { APP_NAME, APP_SUBTITLE, SAMPLE_QUESTIONS } from '@/lib/constants';

const PILLARS = [
  {
    icon: ShieldCheck,
    title: 'Grounded answers',
    body: 'Every response is synthesized from verified university documents and shown with citations you can open.',
    accent: 'bg-sky-500/10 text-sky-600 dark:text-sky-300',
  },
  {
    icon: UserCheck,
    title: 'Role-aware access',
    body: 'Role-based access control ensures students, faculty, and staff only ever see content they’re authorized to.',
    accent: 'bg-indigo-500/10 text-indigo-600 dark:text-indigo-300',
  },
  {
    icon: Cpu,
    title: 'Semantic retrieval',
    body: 'Vector search over embedded policy documents surfaces the most relevant passages for each question.',
    accent: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-300',
  },
];

export default function Home() {
  const token = useAuthStore((s) => s.token);
  const hasHydrated = useAuthStore((s) => s.hasHydrated);
  const authed = hasHydrated && Boolean(token);
  const primaryHref = authed ? '/chat' : '/login';

  return (
    <div className="flex min-h-screen flex-col justify-between bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-sky-600 to-indigo-600 text-white shadow-md shadow-sky-500/20">
              <BookOpen className="h-5 w-5" />
            </div>
            <div>
              <span className="block text-lg font-bold tracking-tight text-foreground">
                {APP_NAME}
              </span>
              <span className="block text-xs font-medium text-muted-foreground">
                {APP_SUBTITLE}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <ThemeToggle />
            {authed ? (
              <Link
                href="/chat"
                className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-sm transition-colors hover:bg-primary/90"
              >
                Open Assistant
                <ArrowRight className="h-4 w-4" />
              </Link>
            ) : (
              <>
                <Link
                  href="/login"
                  className="px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
                >
                  Sign in
                </Link>
                <Link
                  href="/register"
                  className="inline-flex items-center rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-sm transition-colors hover:bg-primary/90"
                >
                  Get started
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Hero */}
      <main className="relative mx-auto flex w-full max-w-7xl flex-1 flex-col items-center justify-center px-6 py-16 text-center">
        {/* Decorative backdrop */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-96 bg-gradient-to-b from-sky-500/5 to-transparent"
        />

        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-sky-200/60 bg-sky-50 px-3 py-1.5 text-xs font-semibold text-sky-700 dark:border-sky-400/20 dark:bg-sky-500/10 dark:text-sky-300">
          <Sparkles className="h-3.5 w-3.5" />
          Retrieval-augmented answers with citations
        </div>

        <h1 className="max-w-4xl text-4xl font-extrabold leading-tight tracking-tight text-foreground sm:text-6xl">
          Citation-backed answers to university policy
        </h1>

        <p className="mt-6 max-w-2xl text-lg leading-relaxed text-muted-foreground sm:text-xl">
          Ask about academic regulations, handbooks, course catalogs, and
          scholarship policies — answered from official Sanctuary University
          sources, with the passages to prove it.
        </p>

        {/* Search box → routes into the app */}
        <Link
          href={primaryHref}
          className="group mt-10 block w-full max-w-2xl"
          aria-label="Open the assistant"
        >
          <div className="relative">
            <div className="flex w-full items-center rounded-2xl border border-border bg-card py-4 pl-12 pr-32 text-left text-muted-foreground shadow-xl shadow-slate-900/5 transition-colors group-hover:border-primary/40">
              <span className="truncate">{SAMPLE_QUESTIONS[0]}</span>
            </div>
            <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
            <span className="absolute right-2.5 top-1/2 inline-flex -translate-y-1/2 items-center gap-1.5 rounded-xl bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground shadow-md transition-colors group-hover:bg-primary/90">
              Ask AI
              <ArrowRight className="h-4 w-4" />
            </span>
          </div>
        </Link>

        {/* Pillars */}
        <div className="mt-20 grid w-full grid-cols-1 gap-6 text-left md:grid-cols-3">
          {PILLARS.map((p) => (
            <div
              key={p.title}
              className="rounded-2xl border border-border bg-card p-6 shadow-sm transition-shadow hover:shadow-md"
            >
              <div
                className={`mb-4 flex h-10 w-10 items-center justify-center rounded-xl ${p.accent}`}
              >
                <p.icon className="h-5 w-5" />
              </div>
              <h3 className="mb-2 text-lg font-bold text-foreground">
                {p.title}
              </h3>
              <p className="text-sm leading-relaxed text-muted-foreground">
                {p.body}
              </p>
            </div>
          ))}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border bg-card py-6">
        <div className="mx-auto max-w-7xl px-6 text-center text-xs text-muted-foreground">
          {APP_SUBTITLE} · {APP_NAME}. For official guidance, always confirm with
          the relevant university office.
        </div>
      </footer>
    </div>
  );
}
