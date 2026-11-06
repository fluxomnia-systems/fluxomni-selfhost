import { existsSync, readFileSync, rmSync, writeFileSync } from 'node:fs';

import { test } from '@playwright/test';

const MARKER = './capture-unavailable.json';

export type InstanceProbe =
  | { ok: true }
  | { ok: false; reason: string };

export async function probeInstance(baseURL: string): Promise<InstanceProbe> {
  try {
    const response = await fetch(`${baseURL}/api/auth/status`);
    if (!response.ok) {
      return {
        ok: false,
        reason: `Fluxomni at ${baseURL} returned HTTP ${response.status}. Point FLUXOMNI_URL at a running v26.4.0 instance to regenerate captures.`,
      };
    }
    return { ok: true };
  } catch (error) {
    const detail = error instanceof Error ? error.message : String(error);
    return {
      ok: false,
      reason: `Fluxomni at ${baseURL} is unreachable (${detail}). Point FLUXOMNI_URL at a running v26.4.0 instance to regenerate captures.`,
    };
  }
}

export function writeCaptureUnavailable(reason: string) {
  writeFileSync(MARKER, JSON.stringify({ reason }));
}

export function clearCaptureUnavailable() {
  rmSync(MARKER, { force: true });
}

export function captureUnavailableReason(): string | null {
  if (!existsSync(MARKER)) return null;
  try {
    const parsed = JSON.parse(readFileSync(MARKER, 'utf8')) as { reason?: string };
    return parsed.reason ?? 'Fluxomni instance is unavailable.';
  } catch {
    return 'Fluxomni instance is unavailable.';
  }
}

export function skipIfCaptureUnavailable() {
  const reason = captureUnavailableReason();
  test.skip(Boolean(reason), reason ?? undefined);
}

/**
 * Skip every test in the file when global setup could not reach Fluxomni.
 * Register this before other hooks so a down instance does not fail CI.
 */
export function gateCapture() {
  test.beforeAll(() => {
    skipIfCaptureUnavailable();
  });
  test.beforeEach(() => {
    skipIfCaptureUnavailable();
  });
}
