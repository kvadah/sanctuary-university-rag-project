import React from 'react';
import { BookOpen, Search, ShieldCheck, Sparkles, UserCheck, Cpu } from 'lucide-react';

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col justify-between">
      {/* Navigation Header */}
      <header className="border-b border-slate-200 bg-white/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-sky-500/20">
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <span className="font-bold text-lg text-slate-900 tracking-tight">KnowledgeHub AI</span>
              <span className="block text-xs font-medium text-slate-500">Sanctuary University</span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <a
              href="/login"
              className="px-4 py-2 text-sm font-medium text-slate-700 hover:text-slate-900 transition-colors"
            >
              Sign In
            </a>
            <a
              href="/chat"
              className="px-4 py-2 text-sm font-medium text-white bg-slate-900 hover:bg-slate-800 rounded-lg shadow-sm transition-all"
            >
              Launch Assistant
            </a>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 max-w-7xl mx-auto px-6 py-16 flex flex-col items-center justify-center text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-sky-50 border border-sky-200/60 text-sky-700 text-xs font-semibold mb-6">
          <Sparkles className="w-3.5 h-3.5" />
          Powered by Retrieval-Augmented Generation (RAG)
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold text-slate-900 tracking-tight max-w-4xl leading-tight">
          Instant, Citation-Backed Answers to University Knowledge
        </h1>

        <p className="mt-6 text-lg sm:text-xl text-slate-600 max-w-2xl leading-relaxed">
          Ask questions about academic regulations, handbooks, course catalogs, scholarship policies, and departmental guides. Grounded exclusively in official university sources.
        </p>

        {/* Demo Search Box Placeholder */}
        <div className="mt-10 w-full max-w-2xl">
          <div className="relative group">
            <input
              type="text"
              readOnly
              placeholder="e.g. What is the minimum GPA required for graduation?"
              className="w-full pl-12 pr-32 py-4 rounded-2xl bg-white border border-slate-200 text-slate-700 shadow-xl shadow-slate-200/50 cursor-pointer focus:outline-none"
            />
            <Search className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
            <button className="absolute right-2.5 top-1/2 -translate-y-1/2 px-5 py-2.5 bg-sky-600 hover:bg-sky-700 text-white font-medium text-sm rounded-xl transition-all shadow-md shadow-sky-600/30">
              Ask AI
            </button>
          </div>
        </div>

        {/* Core Pillars */}
        <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-8 w-full text-left">
          <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-sm hover:shadow-md transition-shadow">
            <div className="w-10 h-10 rounded-xl bg-sky-100 text-sky-700 flex items-center justify-center mb-4">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-slate-900 text-lg mb-2">Zero Hallucinations</h3>
            <p className="text-slate-600 text-sm leading-relaxed">
              Every answer is synthesized directly from verified university documents and policies.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-sm hover:shadow-md transition-shadow">
            <div className="w-10 h-10 rounded-xl bg-indigo-100 text-indigo-700 flex items-center justify-center mb-4">
              <UserCheck className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-slate-900 text-lg mb-2">Role-Aware Security</h3>
            <p className="text-slate-600 text-sm leading-relaxed">
              Role-Based Access Control ensures students, faculty, and administrators only access authorized content.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-sm hover:shadow-md transition-shadow">
            <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center mb-4">
              <Cpu className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-slate-900 text-lg mb-2">Hybrid Retrieval Engine</h3>
            <p className="text-slate-600 text-sm leading-relaxed">
              Combines semantic vector search (Qdrant) with keyword search (BM25) and cross-encoder reranking.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-6">
        <div className="max-w-7xl mx-auto px-6 text-center text-xs text-slate-500">
          © {new Date().getFullYear()} Sanctuary University KnowledgeHub AI. Single-Institution Architecture v1.1.
        </div>
      </footer>
    </div>
  );
}
