'use client';

import { useEffect, useState } from 'react';
import { Save } from 'lucide-react';
import { Dialog } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { useCreateSource, useUpdateSource } from '@/hooks/use-knowledge-sources';
import { useToast } from '@/hooks/use-toast';
import { SOURCE_TYPE_OPTIONS } from '@/lib/constants';
import {
  KnowledgeSource,
  KnowledgeSourceType,
} from '@/lib/types';
import { extractError, titleCase } from '@/lib/utils';

interface SourceFormDialogProps {
  open: boolean;
  onClose: () => void;
  /** When provided, the dialog edits this source; otherwise it creates a new one. */
  source?: KnowledgeSource | null;
}

export function SourceFormDialog({
  open,
  onClose,
  source,
}: SourceFormDialogProps) {
  const isEdit = Boolean(source);
  const create = useCreateSource();
  const update = useUpdateSource();
  const { success, error: toastError } = useToast();
  const pending = create.isPending || update.isPending;

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [sourceType, setSourceType] = useState<KnowledgeSourceType>(
    KnowledgeSourceType.WEB,
  );
  const [isActive, setIsActive] = useState(true);
  const [config, setConfig] = useState('');
  const [configError, setConfigError] = useState<string | null>(null);

  // Reset the form whenever the dialog opens (for the current source or a blank create).
  useEffect(() => {
    if (!open) return;
    setName(source?.name ?? '');
    setDescription(source?.description ?? '');
    setSourceType(source?.source_type ?? KnowledgeSourceType.WEB);
    setIsActive(source?.is_active ?? true);
    setConfig(
      source?.config ? JSON.stringify(source.config, null, 2) : '',
    );
    setConfigError(null);
  }, [open, source]);

  const parseConfig = (): Record<string, unknown> | null | undefined => {
    const trimmed = config.trim();
    if (!trimmed) return null;
    try {
      const parsed = JSON.parse(trimmed);
      if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
        setConfigError('Config must be a JSON object.');
        return undefined;
      }
      return parsed as Record<string, unknown>;
    } catch {
      setConfigError('Config is not valid JSON.');
      return undefined;
    }
  };

  const close = () => {
    if (pending) return;
    onClose();
  };

  const submit = () => {
    if (!name.trim()) {
      toastError('Name required', 'Give the source a name.');
      return;
    }
    setConfigError(null);
    const parsedConfig = parseConfig();
    if (parsedConfig === undefined) return; // invalid JSON

    if (isEdit && source) {
      update.mutate(
        {
          id: source.id,
          body: {
            name: name.trim(),
            description: description.trim() || null,
            config: parsedConfig,
            is_active: isActive,
          },
        },
        {
          onSuccess: () => {
            success('Source updated', `“${name.trim()}” saved.`);
            onClose();
          },
          onError: (err) =>
            toastError('Update failed', extractError(err)),
        },
      );
    } else {
      create.mutate(
        {
          name: name.trim(),
          description: description.trim() || null,
          source_type: sourceType,
          config: parsedConfig,
        },
        {
          onSuccess: () => {
            success('Source created', `“${name.trim()}” added.`);
            onClose();
          },
          onError: (err) =>
            toastError('Creation failed', extractError(err)),
        },
      );
    }
  };

  return (
    <Dialog
      open={open}
      onClose={close}
      title={isEdit ? 'Edit knowledge source' : 'New knowledge source'}
      description={
        isEdit
          ? 'Update the connector’s details.'
          : 'Register a connector the ingestion pipeline can sync from.'
      }
      footer={
        <>
          <Button variant="outline" onClick={close} disabled={pending}>
            Cancel
          </Button>
          <Button onClick={submit} loading={pending}>
            <Save className="h-4 w-4" />
            {isEdit ? 'Save changes' : 'Create source'}
          </Button>
        </>
      }
    >
      <div className="space-y-5">
        <div className="space-y-1.5">
          <Label htmlFor="src-name">Name</Label>
          <Input
            id="src-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Registrar policies"
            disabled={pending}
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="src-desc">Description</Label>
          <Textarea
            id="src-desc"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="What this source contains (optional)"
            rows={2}
            disabled={pending}
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="src-type">Type</Label>
          <Select
            id="src-type"
            value={sourceType}
            onChange={(e) =>
              setSourceType(e.target.value as KnowledgeSourceType)
            }
            disabled={pending || isEdit}
          >
            {SOURCE_TYPE_OPTIONS.map((t) => (
              <option key={t} value={t}>
                {titleCase(t)}
              </option>
            ))}
          </Select>
          {isEdit && (
            <p className="text-xs text-muted-foreground">
              The source type can’t be changed after creation.
            </p>
          )}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="src-config">Config (JSON)</Label>
          <Textarea
            id="src-config"
            value={config}
            onChange={(e) => setConfig(e.target.value)}
            placeholder={'{\n  "url": "https://…"\n}'}
            rows={4}
            spellCheck={false}
            className="font-mono text-xs"
            disabled={pending}
          />
          {configError ? (
            <p className="text-xs text-destructive">{configError}</p>
          ) : (
            <p className="text-xs text-muted-foreground">
              Optional connector settings. Leave blank if not needed.
            </p>
          )}
        </div>

        {isEdit && (
          <label className="flex items-center gap-2 text-sm text-foreground">
            <input
              type="checkbox"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
              disabled={pending}
              className="h-4 w-4 rounded border-input text-primary focus:ring-ring"
            />
            Active
          </label>
        )}
      </div>
    </Dialog>
  );
}
