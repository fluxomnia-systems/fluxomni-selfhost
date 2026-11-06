import { resolve } from 'node:path';

import { expect, test, type Page } from '@playwright/test';

import { createAuthenticatedApi } from '../helpers/auth';
import { captureUnavailableReason, gateCapture, skipIfCaptureUnavailable } from '../helpers/instance';
import { holdCallout, smoothClick } from '../helpers/pacing';
import { saveRecordedVideo } from '../helpers/video';
import {
  captureStill,
  expandPlaylistSettings,
  futureSchedule,
  openPlaylistWorkspace,
  openRecordedPage,
  v264VideoDir,
} from '../helpers/v264-ui';
import {
  cleanupV264,
  probeV264Api,
  seedV264Scenario,
  type V264Scenario,
} from '../helpers/v264-seed';

/**
 * Playlist programming on a suite-owned route: stinger, planned timing,
 * a future weekday schedule, readiness, and the timestamp cue when it is enabled.
 * Playback is not started, and preparation jobs are not submitted.
 */

gateCapture();

let scenario: V264Scenario | undefined;
let seeded = false;

test.beforeAll(async () => {
  skipIfCaptureUnavailable();
  const api = await createAuthenticatedApi(process.env.FLUXOMNI_URL ?? 'http://localhost');
  try {
    try {
      await probeV264Api(api);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      test.skip(
        /cannot query field .rundowns/i.test(message),
        'This instance has no v26.4.0 playlist API. Regenerate captures against Fluxomni v26.4.0.',
      );
      throw error;
    }
    await cleanupV264(api);
    scenario = await seedV264Scenario(api);
    seeded = true;
  } finally {
    await api.dispose();
  }
});

test.afterAll(async () => {
  if (!seeded || captureUnavailableReason()) return;
  const api = await createAuthenticatedApi(process.env.FLUXOMNI_URL ?? 'http://localhost');
  try {
    await cleanupV264(api);
  } finally {
    await api.dispose();
  }
});

test('playlist-timing.jpg — planned durations and total', async ({ page }) => {
  const data = requiredScenario();
  await openPlaylistWorkspace(page, data.programRoute.id);
  await expandPlaylistSettings(page);
  await expect(page.getByTestId('playlist-item-timing').first()).toBeVisible({ timeout: 15_000 });
  await captureStill(page, 'playlist-timing');
});

test('playlist-stinger.jpg — choose a boundary clip', async ({ page }) => {
  const data = requiredScenario();
  await openPlaylistWorkspace(page, data.programRoute.id);
  await expandPlaylistSettings(page);
  const stinger = page.getByLabel('Playlist stinger');
  await stinger.scrollIntoViewIfNeeded();
  await expect(stinger).toBeVisible({ timeout: 15_000 });
  const choose = stinger.getByRole('button', { name: /choose clip|change clip/i });
  await choose.click();
  const picker = page.getByTestId('playlist-stinger-picker');
  await expect(picker).toBeVisible();
  await picker.getByText(data.videoNames[0], { exact: true }).first().click();
  await expect(stinger.getByText(data.videoNames[0]).first()).toBeVisible({ timeout: 15_000 });
  const enable = stinger.getByLabel('Enable playlist stinger');
  if (!(await enable.isChecked())) await enable.check();
  await expect(enable).toBeChecked();
  await captureStill(page, 'playlist-stinger');
});

test('playlist-schedule.jpg — weekday schedule, zone, and next start', async ({ page }) => {
  const data = requiredScenario();
  await openPlaylistWorkspace(page, data.programRoute.id);
  await expandPlaylistSettings(page);
  await armWeekdaySchedule(page, data.programRoute.id);
  await expect(page.getByTestId('route-playlist-schedule-banner')).toBeVisible({
    timeout: 15_000,
  });
  await expect(page.getByText(/next:/i).first()).toBeVisible();
  await captureStill(page, 'playlist-schedule');
});

test('route-readiness.jpg — checklist without starting streams', async ({ page }) => {
  const data = requiredScenario();
  await openPlaylistWorkspace(page, data.programRoute.id);
  const checklist = await openReadinessChecklist(page);
  const flow = page.getByLabel('Intended flow');
  if (await flow.isVisible().catch(() => false)) {
    await flow.selectOption({ label: 'Playlist' });
  }
  await expect(checklist.getByRole('button', { name: 'Refresh readiness' })).toBeVisible();
  await captureStill(page, 'route-readiness');
});

test('playlist-cue.jpg — timestamp editor when playback cueing is enabled', async ({ page }) => {
  const data = requiredScenario();
  await openPlaylistWorkspace(page, data.programRoute.id);
  const editTime = page.getByRole('button', { name: 'Edit playback time' });
  const progress = page.getByTestId('playlist-progress').first();
  await expect(progress).toBeVisible({ timeout: 15_000 });
  if (!(await editTime.isVisible().catch(() => false)) || !(await editTime.isEnabled())) {
    test.info().annotations.push({
      type: 'gap',
      description:
        'Timestamp cue stayed disabled because playback is not confirmed. The suite does not start playout to force it.',
    });
    await captureStill(page, 'playlist-cue');
    return;
  }
  await editTime.click();
  const editor = page.getByRole('form', { name: 'Edit playback time' });
  await expect(editor).toBeVisible();
  await editor.getByLabel('Playback timestamp').fill('00:01.000');
  await captureStill(page, 'playlist-cue');
  await page.getByRole('button', { name: 'Cancel time edit' }).click();
});

test('playlist-prepare.jpg — preparation option, job not started', async ({ page }) => {
  const data = requiredScenario();
  await openPlaylistWorkspace(page, data.programRoute.id);
  await page.getByTestId('playlist-expand-picker').click();
  await expect(page.getByRole('heading', { name: 'Add to playlist' })).toBeVisible({
    timeout: 10_000,
  });
  const preparation = page.locator('details').filter({ hasText: 'Playback preparation' }).first();
  if (!(await preparation.isVisible().catch(() => false))) {
    test.info().annotations.push({
      type: 'gap',
      description:
        'Playback preparation stays hidden until the route has a baseline profile. The checkbox was not checked, and Normalize files was not used.',
    });
    test.skip(true, 'Playback preparation is not available for this route.');
  }
  if (!(await preparation.evaluate((node) => (node as HTMLDetailsElement).open))) {
    await preparation.locator('summary').click();
  }
  const checkbox = preparation.getByRole('checkbox');
  await expect(checkbox).not.toBeChecked();
  await expect(preparation.getByText('Prepare selected videos for this baseline')).toBeVisible();
  await preparation.scrollIntoViewIfNeeded();
  await captureStill(page, 'playlist-prepare');
  await page.keyboard.press('Escape');
});

test('playlist-programming.webm — stinger, timing, and schedule', async ({ browser }) => {
  test.setTimeout(180_000);
  const data = requiredScenario();
  const videoDir = test.info().outputPath('videos');
  const { context, page } = await openRecordedPage(browser, videoDir);
  try {
    await openPlaylistWorkspace(page, data.programRoute.id);
    await expandPlaylistSettings(page);
    const timing = page.getByTestId('playlist-timing-summary');
    await holdCallout(page, timing, 'Planned program total', 'right', 1100);
    const stinger = page.getByLabel('Playlist stinger');
    await holdCallout(page, stinger, 'Optional stinger', 'left', 900);
    const choose = stinger.getByRole('button', { name: /choose clip|change clip/i });
    await smoothClick(page, choose);
    const picker = page.getByTestId('playlist-stinger-picker');
    await expect(picker).toBeVisible();
    await picker.getByText(data.videoNames[0], { exact: true }).first().click();
    await expect(stinger.getByText(data.videoNames[0]).first()).toBeVisible({ timeout: 15_000 });
    if (await picker.isVisible().catch(() => false)) await page.keyboard.press('Escape');
    await armWeekdaySchedule(page, data.programRoute.id);
    await holdCallout(
      page,
      page.getByTestId('route-playlist-schedule-banner'),
      'Next occurrence',
      'left',
      1300,
    );
    const checklist = await openReadinessChecklist(page);
    await holdCallout(page, checklist, 'Readiness checklist', 'right', 1100);
    await page.waitForTimeout(700);
  } finally {
    await saveRecordedVideo(
      page,
      context,
      resolve(v264VideoDir(), 'playlist-programming.webm'),
      { trimStartSeconds: 2 },
    );
  }
});

function requiredScenario(): V264Scenario {
  if (!scenario) throw new Error('v26.4.0 scenario was not seeded');
  return scenario;
}

async function openReadinessChecklist(page: Page) {
  const details = page.locator('details.readiness-panel').first();
  await expect(details).toBeVisible({ timeout: 15_000 });
  await details.scrollIntoViewIfNeeded();
  if (!(await details.evaluate((node) => (node as HTMLDetailsElement).open))) {
    await details.locator('> summary').click();
  }
  const checklist = page.getByLabel('Route readiness checklist');
  await expect(checklist).toBeVisible({ timeout: 15_000 });
  await checklist.scrollIntoViewIfNeeded();
  return checklist;
}

async function armWeekdaySchedule(page: Page, routeId: string) {
  const details = page.locator('details.playlist-schedule-details').first();
  await details.scrollIntoViewIfNeeded();
  if (!(await details.evaluate((node) => (node as HTMLDetailsElement).open))) {
    await details.locator('summary').click();
  }
  const repeat = page.locator(`[id="schedule-repeat-${cssAttr(routeId)}"]`);
  await expect(repeat).toBeVisible({ timeout: 10_000 });
  await repeat.selectOption({ label: 'Selected weekdays' });
  const zone = page.locator(`[id="playlist-schedule-zone-${cssAttr(routeId)}"]`);
  const preferredZone = 'Europe/Bratislava';
  const timeZone = await zone.evaluate((select, preferred) => {
    const options = Array.from((select as HTMLSelectElement).options);
    const found =
      options.find((option) => option.value === preferred || option.text.trim() === preferred) ??
      options.find((option) => option.value.includes('/')) ??
      options.find((option) => option.value.trim());
    return found?.value ?? '';
  }, preferredZone);
  if (!timeZone) throw new Error('Playlist schedule did not offer a time zone');
  await zone.selectOption(timeZone);
  const when = futureSchedule(timeZone);
  const date = page.locator(`[id="playlist-schedule-date-${cssAttr(routeId)}"]`);
  if (await date.isVisible().catch(() => false)) await date.fill(when.date);
  await page.locator(`[id="playlist-schedule-time-${cssAttr(routeId)}"]`).fill(when.time);
  const weekdays = page.getByRole('group', { name: 'Weekdays' });
  if (await weekdays.isVisible().catch(() => false)) {
    const monday = weekdays.getByRole('checkbox').first();
    if (!(await monday.isChecked())) await monday.check();
  }
  const save = details.getByRole('button', { name: /^(Schedule|Save changes)$/ });
  await save.click();
  await expect(page.getByText(/unable to update the schedule/i)).toHaveCount(0);
}

function cssAttr(value: string): string {
  return value.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
}
