import { expect, test, type Locator, type Page } from '@playwright/test';

import { createAuthenticatedApi } from '../helpers/auth';
import { captureUnavailableReason, gateCapture, skipIfCaptureUnavailable } from '../helpers/instance';
import { waitForAppReady } from '../helpers/readiness';
import { captureStill } from '../helpers/v264-ui';
import {
  cleanupV264,
  listRecordingNames,
  probeV264Api,
  seedV264Scenario,
  V264_PREFIX,
  type V264Scenario,
} from '../helpers/v264-seed';

/**
 * Library surfaces added in v26.4.0: slideshow composition, automatic
 * thumbnails, and recording preserve / preview when a recording already exists.
 * The suite does not render a slideshow or preserve a recording.
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
        'This instance has no v26.4.0 Library API. Regenerate captures against Fluxomni v26.4.0.',
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

test('artifacts-slideshow.jpg — photo order and default timing, render not started', async ({
  page,
}) => {
  const data = requiredScenario();
  await page.goto('/artifacts');
  await waitForAppReady(page);
  await page.getByTestId('artifact-picker-add-menu').click();
  const fromPhotos = page.getByRole('button', { name: 'Video from photos' });
  await expect(fromPhotos).toBeVisible({ timeout: 10_000 });
  await fromPhotos.click();
  const legacy = page
    .locator('[role="dialog"], .modal, dialog')
    .filter({ hasText: 'Choose photos in order' })
    .first();
  if (await legacy.isVisible().catch(() => false)) {
    await composeLegacySlideshow(legacy, data.photoNames[0]);
  } else {
    await composeSlideshowDialog(page, data.photoNames[0]);
  }
  await captureStill(page, 'artifacts-slideshow');
  await page.keyboard.press('Escape');
});

test('artifacts-thumbnails.jpg — library thumbnail state for an uploaded video', async ({
  page,
}) => {
  const data = requiredScenario();
  await page.goto('/artifacts');
  await waitForAppReady(page);
  const search = page.getByLabel('Search artifacts');
  await search.fill(data.videoNames[0]);
  await expect(page.getByText(data.videoNames[0]).first()).toBeVisible({ timeout: 15_000 });
  const status = page.locator('[data-thumbnail-status]').first();
  await expect(status).toBeVisible({ timeout: 15_000 });
  const deadline = Date.now() + 20_000;
  let value = await status.getAttribute('data-thumbnail-status');
  while (value === 'PENDING' && Date.now() < deadline) {
    await page.waitForTimeout(1000);
    value = await status.getAttribute('data-thumbnail-status');
  }
  await captureStill(page, 'artifacts-thumbnails');
});

test('artifacts-recording.jpg — preserve and preview when a recording exists', async ({
  page,
}) => {
  const api = await createAuthenticatedApi(process.env.FLUXOMNI_URL ?? 'http://localhost');
  let recordingName = '';
  try {
    const names = await listRecordingNames(api);
    recordingName = names[0] ?? '';
  } finally {
    await api.dispose();
  }
  if (!recordingName) {
    test.info().annotations.push({
      type: 'gap',
      description:
        'No Library recording was present. Preserve, FLV preview, and retention states are not synthesized.',
    });
    test.skip(true, 'No Library recording is available to preview.');
  }

  await page.goto('/artifacts');
  await waitForAppReady(page);
  await page.getByLabel('Search artifacts').fill(recordingName);
  const rowName = page.getByText(recordingName, { exact: true }).first();
  await expect(rowName).toBeVisible({ timeout: 15_000 });
  const preview = page.getByTestId('artifact-row-preview').first();
  if (await preview.isVisible().catch(() => false)) {
    await preview.click();
    await page.waitForTimeout(800);
  }
  const preserve = page.getByRole('button', { name: /preserve to library|retry preservation/i });
  if (!(await preserve.isVisible().catch(() => false))) {
    test.info().annotations.push({
      type: 'gap',
      description:
        'A recording row was visible, but the preserve control was not. The preview was captured without starting preservation.',
    });
  }
  await captureStill(page, 'artifacts-recording');
  await page.keyboard.press('Escape');
});

function requiredScenario(): V264Scenario {
  if (!scenario) throw new Error('v26.4.0 scenario was not seeded');
  return scenario;
}

async function composeLegacySlideshow(composer: Locator, photoName: string) {
  const photo = composer.getByText(photoName, { exact: true }).first();
  await expect(photo).toBeVisible({ timeout: 15_000 });
  await photo.click();
  const timing = composer.getByText('Name and timing', { exact: true });
  if (await timing.isVisible().catch(() => false)) await timing.click();
  await fillSlideshowTiming(composer);
}

async function composeSlideshowDialog(page: Page, photoName: string) {
  const composer = page.getByRole('dialog', { name: 'Create video' });
  await expect(composer).toBeVisible({ timeout: 10_000 });
  const choose = composer.getByRole('button', { name: 'Choose from Library' });
  await expect(choose).toBeVisible();
  await expect
    .poll(async () => composer.getByText('Checking object storage…').isVisible().catch(() => false), {
      timeout: 15_000,
    })
    .toBe(false);
  if (await choose.isEnabled().catch(() => false)) {
    await choose.click();
    const search = composer.getByLabel('Search images');
    if (await search.isVisible().catch(() => false)) await search.fill(photoName);
    const photo = composer.getByRole('button', { name: `Select image ${photoName}` });
    await expect(photo).toBeVisible({ timeout: 15_000 });
    await photo.click();
  } else {
    test.info().annotations.push({
      type: 'gap',
      description:
        'The slideshow composer opened, but photo selection stayed disabled. Create video was not used.',
    });
  }
  const timing = composer.getByText('Name and timing', { exact: true });
  if (await timing.isVisible().catch(() => false)) await timing.click();
  const videoName = composer.getByLabel('Video name');
  if (await videoName.isEnabled().catch(() => false)) {
    await fillSlideshowTiming(composer);
  }
  await expect(composer.getByRole('button', { name: /^Create video$/ })).toBeVisible();
}

async function fillSlideshowTiming(composer: Locator) {
  const videoName = composer.getByLabel('Video name');
  await expect(videoName).toBeVisible();
  await videoName.fill(`${V264_PREFIX} photo reel`);
  const seconds = composer.getByLabel('Seconds per image');
  await expect(seconds).toBeVisible();
  const current = Number(await seconds.inputValue());
  if (!Number.isFinite(current) || current <= 0) await seconds.fill('5');
  await expect.poll(async () => Number(await seconds.inputValue())).toBe(5);
}
