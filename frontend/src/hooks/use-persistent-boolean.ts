'use client';

import { useCallback, useEffect, useState } from 'react';

type SetBoolean = (next: boolean | ((prev: boolean) => boolean)) => void;

/**
 * A boolean state hook backed by localStorage.
 *
 * Renders `initial` on the server and first client paint, then reconciles with
 * any persisted value inside an effect — this avoids an SSR/client hydration
 * mismatch (the DOM matches on first render, then updates after mount).
 */
export function usePersistentBoolean(
  key: string,
  initial: boolean,
): readonly [boolean, SetBoolean] {
  const [value, setValue] = useState(initial);

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(key);
      if (stored !== null) setValue(stored === '1');
    } catch {
      // Storage may be unavailable (private mode, disabled cookies) — ignore.
    }
  }, [key]);

  const update = useCallback<SetBoolean>(
    (next) => {
      setValue((prev) => {
        const resolved = typeof next === 'function' ? next(prev) : next;
        try {
          window.localStorage.setItem(key, resolved ? '1' : '0');
        } catch {
          // Ignore write failures; state still updates in memory.
        }
        return resolved;
      });
    },
    [key],
  );

  return [value, update] as const;
}
