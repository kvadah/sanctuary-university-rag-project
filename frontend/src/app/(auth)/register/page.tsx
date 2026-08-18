'use client';

import { useState } from 'react';
import Link from 'next/link';
import { AuthCard } from '@/components/auth/auth-card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useRegister } from '@/hooks/use-auth';
import { useToast } from '@/hooks/use-toast';
import { extractError } from '@/lib/utils';

export default function RegisterPage() {
  const register = useRegister();
  const { error: toastError } = useToast();
  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    department: '',
  });

  const set = <K extends keyof typeof form>(key: K, value: (typeof form)[K]) =>
    setForm((f) => ({ ...f, [key]: value }));

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    register.mutate(
      {
        first_name: form.first_name,
        last_name: form.last_name,
        email: form.email,
        password: form.password,
        department: form.department || null,
      },
      {
        onError: (err) =>
          toastError(
            'Registration failed',
            extractError(err, 'Please review your details and try again.'),
          ),
      },
    );
  };

  return (
    <AuthCard
      title="Create your account"
      subtitle="Get started with the KnowledgeHub assistant"
      footer={
        <>
          Already have an account?{' '}
          <Link
            href="/login"
            className="font-medium text-primary hover:underline"
          >
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <Label htmlFor="first_name">First name</Label>
            <Input
              id="first_name"
              required
              autoComplete="given-name"
              value={form.first_name}
              onChange={(e) => set('first_name', e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="last_name">Last name</Label>
            <Input
              id="last_name"
              required
              autoComplete="family-name"
              value={form.last_name}
              onChange={(e) => set('last_name', e.target.value)}
            />
          </div>
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            required
            autoComplete="email"
            placeholder="you@sanctuary.edu"
            value={form.email}
            onChange={(e) => set('email', e.target.value)}
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            required
            minLength={8}
            autoComplete="new-password"
            placeholder="At least 8 characters"
            value={form.password}
            onChange={(e) => set('password', e.target.value)}
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="department">Department</Label>
          <Input
            id="department"
            placeholder="Optional"
            value={form.department}
            onChange={(e) => set('department', e.target.value)}
          />
        </div>

        <Button
          type="submit"
          className="w-full"
          loading={register.isPending}
        >
          Create account
        </Button>
      </form>
    </AuthCard>
  );
}
