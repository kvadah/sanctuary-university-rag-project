'use client';

import { LogOut, Mail, Building2, Shield } from 'lucide-react';
import { ThemeSegmented } from '@/components/ui/theme-toggle';
import { Avatar } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { useAuthStore } from '@/stores/auth-store';
import { useLogout } from '@/hooks/use-auth';
import { fullName, roleLabel, formatDate } from '@/lib/utils';

function InfoRow({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Mail;
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="flex items-center gap-3 py-3">
      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-muted text-muted-foreground">
        <Icon className="h-4 w-4" />
      </span>
      <div className="min-w-0">
        <p className="text-xs text-muted-foreground">{label}</p>
        <div className="truncate text-sm font-medium text-foreground">
          {value}
        </div>
      </div>
    </div>
  );
}

export default function SettingsPage() {
  const user = useAuthStore((s) => s.user);
  const logout = useLogout();

  return (
    <div className="mx-auto w-full max-w-2xl px-4 py-6 sm:px-6 lg:px-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          Settings
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Manage your profile and appearance.
        </p>
      </div>

      <div className="mt-6 space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Profile</CardTitle>
          </CardHeader>
          <CardContent>
            {user ? (
              <>
                <div className="flex items-center gap-4">
                  <Avatar
                    first={user.first_name}
                    last={user.last_name}
                    className="h-14 w-14 text-lg"
                  />
                  <div className="min-w-0">
                    <p className="truncate text-lg font-semibold text-foreground">
                      {fullName(user)}
                    </p>
                    <Badge variant="secondary" className="mt-1">
                      {roleLabel(user.role)}
                    </Badge>
                  </div>
                </div>
                <div className="mt-4 divide-y divide-border border-t pt-2">
                  <InfoRow icon={Mail} label="Email" value={user.email} />
                  <InfoRow
                    icon={Shield}
                    label="Role"
                    value={roleLabel(user.role)}
                  />
                  <InfoRow
                    icon={Building2}
                    label="Department"
                    value={user.department || '—'}
                  />
                  <InfoRow
                    icon={Shield}
                    label="Member since"
                    value={formatDate(user.created_at)}
                  />
                </div>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">
                Loading your profile…
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Appearance</CardTitle>
            <CardDescription>
              Choose a theme. “System” follows your device setting.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ThemeSegmented />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Session</CardTitle>
            <CardDescription>
              Sign out of KnowledgeHub AI on this device.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="outline" onClick={logout}>
              <LogOut className="h-4 w-4" />
              Log out
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
