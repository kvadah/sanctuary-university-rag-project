import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'KnowledgeHub AI — Sanctuary University',
  description: 'AI Knowledge Assistant for Sanctuary University students, faculty, and staff.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased text-slate-900 bg-slate-50">
        {children}
      </body>
    </html>
  );
}
