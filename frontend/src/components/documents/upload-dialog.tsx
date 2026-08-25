'use client';

import { useRef, useState } from 'react';
import { UploadCloud, FileUp, X } from 'lucide-react';
import { Dialog } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select } from '@/components/ui/select';
import { useUploadDocument } from '@/hooks/use-documents';
import { useToast } from '@/hooks/use-toast';
import { assignableClassifications, ACADEMIC_TERMS } from '@/lib/constants';
import { DocumentClassification, UserRole } from '@/lib/types';
import { classificationMeta, extractError } from '@/lib/utils';

interface UploadDialogProps {
  open: boolean;
  onClose: () => void;
  role: UserRole;
}

const MAX_MB = 25;

export function UploadDialog({ open, onClose, role }: UploadDialogProps) {
  const options = assignableClassifications(role);
  const inputRef = useRef<HTMLInputElement>(null);

  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [classification, setClassification] = useState<DocumentClassification>(
    options[0] ?? DocumentClassification.PUBLIC,
  );
  const [term, setTerm] = useState('');
  const [dragging, setDragging] = useState(false);

  const upload = useUploadDocument();
  const { success, error: toastError } = useToast();

  const reset = () => {
    setFile(null);
    setTitle('');
    setClassification(options[0] ?? DocumentClassification.PUBLIC);
    setTerm('');
  };

  const close = () => {
    if (upload.isPending) return;
    reset();
    onClose();
  };

  const pick = (f: File | null | undefined) => {
    if (!f) return;
    if (f.size > MAX_MB * 1024 * 1024) {
      toastError('File too large', `Maximum size is ${MAX_MB} MB.`);
      return;
    }
    setFile(f);
    if (!title) setTitle(f.name.replace(/\.[^.]+$/, ''));
  };

  const submit = () => {
    if (!file) return;
    upload.mutate(
      {
        file,
        title: title.trim() || undefined,
        classification,
        academic_term: term || undefined,
      },
      {
        onSuccess: (job) => {
          success(
            'Indexing started',
            `“${job.original_filename ?? file.name}” will appear in the list once processing finishes.`,
          );
          reset();
          onClose();
        },
        onError: (err) =>
          toastError('Upload failed', extractError(err, 'Please try again.')),
      },
    );
  };

  return (
    <Dialog
      open={open}
      onClose={close}
      title="Upload document"
      description="Files are parsed, chunked, and embedded for retrieval."
      footer={
        <>
          <Button variant="outline" onClick={close} disabled={upload.isPending}>
            Cancel
          </Button>
          <Button onClick={submit} loading={upload.isPending} disabled={!file}>
            <UploadCloud className="h-4 w-4" />
            Upload &amp; index
          </Button>
        </>
      }
    >
      <div className="space-y-5">
        <div>
          <input
            ref={inputRef}
            type="file"
            className="sr-only"
            accept=".pdf,.docx,.doc,.txt,.md,.pptx,.xlsx,.csv"
            onChange={(e) => pick(e.target.files?.[0])}
          />
          {file ? (
            <div className="flex items-center gap-3 rounded-xl border bg-muted/40 p-3">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <FileUp className="h-5 w-5" />
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-foreground">
                  {file.name}
                </p>
                <p className="text-xs text-muted-foreground">
                  {(file.size / 1024).toFixed(0)} KB
                </p>
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => setFile(null)}
                aria-label="Remove file"
                disabled={upload.isPending}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              onDragOver={(e) => {
                e.preventDefault();
                setDragging(true);
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDragging(false);
                pick(e.dataTransfer.files?.[0]);
              }}
              className={`flex w-full flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed px-6 py-8 text-center transition-colors ${
                dragging
                  ? 'border-primary bg-primary/5'
                  : 'border-border hover:border-primary/40 hover:bg-muted/40'
              }`}
            >
              <UploadCloud className="h-8 w-8 text-muted-foreground" />
              <span className="text-sm font-medium text-foreground">
                Click to browse or drag a file here
              </span>
              <span className="text-xs text-muted-foreground">
                PDF, DOCX, PPTX, XLSX, TXT · up to {MAX_MB} MB
              </span>
            </button>
          )}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="doc-title">Title</Label>
          <Input
            id="doc-title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Defaults to the file name"
            disabled={upload.isPending}
          />
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="doc-classification">Access level</Label>
            <Select
              id="doc-classification"
              value={classification}
              onChange={(e) =>
                setClassification(e.target.value as DocumentClassification)
              }
              disabled={upload.isPending}
            >
              {options.map((c) => (
                <option key={c} value={c}>
                  {classificationMeta(c).label}
                </option>
              ))}
            </Select>
            <p className="text-xs text-muted-foreground">
              Who may retrieve this document.
            </p>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="doc-term">Academic term</Label>
            <Select
              id="doc-term"
              value={term}
              onChange={(e) => setTerm(e.target.value)}
              disabled={upload.isPending}
            >
              <option value="">Not term-specific</option>
              {ACADEMIC_TERMS.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </Select>
          </div>
        </div>
      </div>
    </Dialog>
  );
}
