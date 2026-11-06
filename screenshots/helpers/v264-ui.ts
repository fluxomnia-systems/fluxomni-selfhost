import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { expect, type Browser, type Page } from '@playwright/test';

import { waitForAppReady } from './readiness';
import { redactLabSecrets } from './redact';

const __dirname = dirname(fileURLToPath(import.meta.url));

export const V264_IMAGES_DIR = resolve(
  __dirname,
  '../../docs/src/images/user-guide/v264',
);

export function v264VideoDir(): string {
  return process.env.FLUXOMNI_VIDEO_OUTPUT_DIR
    ? resolve(process.env.FLUXOMNI_VIDEO_OUTPUT_DIR)
    : resolve(__dirname, '../recordings/user-guide');
}

export async function captureStill(page: Page, name: string) {
  await page.waitForTimeout(300);
  await redactLabSecrets(page);
  await page.screenshot({
    path: resolve(V264_IMAGES_DIR, `${name}.jpg`),
    type: 'jpeg',
    quality: 90,
  });
}

export async function openPlaylistWorkspace(page: Page, routeId: string) {
  await page.goto(`/routes/${routeId}`);
  await waitForAppReady(page);
  const viewSelector = page.locator('button.workspace-mode-trigger').first();
  if (await viewSelector.isVisible().catch(() => false)) {
    await viewSelector.click();
    const playlistOption = page
      .locator('button.workspace-mode-option')
      .filter({ hasText: 'Playlist Playout' })
      .first();
    await expect(playlistOption).toBeVisible({ timeout: 10_000 });
    await playlistOption.click();
  }
  await expect(page.locator('#playlist-panel')).toBeVisible({ timeout: 20_000 });
  await redactLabSecrets(page);
}

export async function expandPlaylistSettings(page: Page) {
  const summary = page.getByText('Playlist settings', { exact: false }).first();
  await summary.scrollIntoViewIfNeeded();
  const details = page.locator('details.playlist-settings').first();
  if ((await details.count()) > 0 && !(await details.evaluate((node) => (node as HTMLDetailsElement).open))) {
    await summary.click();
  }
  await expect(page.getByTestId('playlist-timing-summary')).toBeVisible({ timeout: 10_000 });
}

export async function openRecordedPage(browser: Browser, videoDir: string) {
  const context = await browser.newContext({
    baseURL: process.env.FLUXOMNI_URL ?? 'http://localhost',
    storageState: resolve(__dirname, '../auth-state.json'),
    viewport: { width: 1280, height: 720 },
    recordVideo: {
      dir: videoDir,
      size: { width: 1280, height: 720 },
    },
  });
  const page = await context.newPage();
  return { context, page };
}

export function futureSchedule(timeZone: string): { date: string; time: string } {
  const target = new Date(Date.now() + 6 * 60 * 60 * 1000);
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  }).formatToParts(target);
  const read = (type: Intl.DateTimeFormatPartTypes) =>
    parts.find((part) => part.type === type)?.value ?? '00';
  return {
    date: `${read('year')}-${read('month')}-${read('day')}`,
    time: `${read('hour')}:${read('minute')}`,
  };
}
