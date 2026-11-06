import { resolve } from 'node:path';

import { expect, test, type Page } from '@playwright/test';

import { createAuthenticatedApi } from '../helpers/auth';
import { captureUnavailableReason, gateCapture, skipIfCaptureUnavailable } from '../helpers/instance';
import { holdCallout, smoothClick, smoothFill } from '../helpers/pacing';
import { waitForAppReady } from '../helpers/readiness';
import { saveRecordedVideo } from '../helpers/video';
import {
  captureStill,
  expandPlaylistSettings,
  openPlaylistWorkspace,
  openRecordedPage,
  v264VideoDir,
} from '../helpers/v264-ui';
import {
  cleanupV264,
  probeV264Api,
  seedV264Scenario,
  V264_RUNDOWN_NAME,
  type V264Scenario,
} from '../helpers/v264-seed';

/**
 * Rundowns page: list, edit, duplicate, and apply one saved revision onto a
 * suite-owned idle route. Apply is never pointed at an existing lab route.
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
        'This instance has no Rundowns API. Regenerate captures against Fluxomni v26.4.0.',
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

test('rundowns.jpg — saved rundown list and editor', async ({ page }) => {
  const data = requiredScenario();
  await editRundown(page, data);
  await captureStill(page, 'rundowns');
});

test('rundown-duplicate.jpg — duplicated saved revision', async ({ page }) => {
  const data = requiredScenario();
  await editRundown(page, data);
  await page.getByRole('button', { name: 'Duplicate', exact: true }).click();
  await expect(page.getByText(/independent copy created/i)).toBeVisible({ timeout: 15_000 });
  await expect(page.getByText(`${V264_RUNDOWN_NAME} copy`).first()).toBeVisible();
  await captureStill(page, 'rundown-duplicate');
});

test('rundown-apply.jpg — apply revision to an idle suite route', async ({ page }) => {
  const data = requiredScenario();
  await editRundown(page, data);
  await openPlaylistWorkspace(page, data.applyRoute.id);
  await expandPlaylistSettings(page);
  const summary = page.locator('summary').filter({ hasText: 'Reusable rundown' }).first();
  await summary.scrollIntoViewIfNeeded();
  const settings = summary.locator('xpath=ancestor::details[1]');
  if (!(await settings.evaluate((node) => (node as HTMLDetailsElement).open))) {
    await summary.click();
  }
  await expect(page.getByText(/apply copies a saved revision/i)).toBeVisible();
  const picker = page.getByLabel('Saved rundown');
  await expect(picker).toBeVisible();
  const option = picker.locator('option', { hasText: V264_RUNDOWN_NAME });
  await expect(option).toBeAttached({ timeout: 15_000 });
  const label = (await option.first().textContent())?.trim() ?? '';
  if (!label) throw new Error(`Saved rundown ${V264_RUNDOWN_NAME} was not listed`);
  await picker.selectOption({ label });
  const apply = page.getByRole('button', { name: 'Apply rundown' });
  await expect(apply).toBeEnabled({ timeout: 10_000 });
  await apply.click();
  await expect(page.getByText(/applied/i).first()).toBeVisible({ timeout: 15_000 });
  await captureStill(page, 'rundown-apply');
});

test('rundowns.webm — create, save, and duplicate a rundown', async ({ browser }) => {
  test.setTimeout(150_000);
  const data = requiredScenario();
  const videoDir = test.info().outputPath('videos');
  const { context, page } = await openRecordedPage(browser, videoDir);
  try {
    await editRundown(page, data, {
      paced: true,
      name: `${V264_RUNDOWN_NAME} walkthrough`,
    });
    const duplicate = page.getByRole('button', { name: 'Duplicate', exact: true });
    await holdCallout(page, duplicate, 'Duplicate the revision', 'left', 900);
    await smoothClick(page, duplicate);
    await expect(page.getByText(/independent copy created/i)).toBeVisible({ timeout: 15_000 });
    await holdCallout(
      page,
      page.getByText(`${V264_RUNDOWN_NAME} walkthrough copy`).first(),
      'Independent copy',
      'right',
      1200,
    );
    await page.waitForTimeout(800);
  } finally {
    await saveRecordedVideo(page, context, resolve(v264VideoDir(), 'rundowns.webm'), {
      trimStartSeconds: 2,
    });
  }
});

function requiredScenario(): V264Scenario {
  if (!scenario) throw new Error('v26.4.0 scenario was not seeded');
  return scenario;
}

async function editRundown(
  page: Page,
  data: V264Scenario,
  options: { paced?: boolean; name?: string } = {},
) {
  const rundownName = options.name ?? V264_RUNDOWN_NAME;
  await page.goto('/rundowns');
  await waitForAppReady(page);
  await expect(page.getByRole('link', { name: /^rundowns$/i })).toBeVisible();
  const existing = page.getByText(rundownName, { exact: true }).first();
  if (await existing.isVisible().catch(() => false)) {
    await existing.click();
    await expect(page.getByLabel('Program order')).toBeVisible();
    return;
  }
  {
    const create = page.getByRole('button', { name: 'New rundown' }).first();
    if (options.paced) await holdCallout(page, create, 'New rundown', 'left', 800);
    await create.click();
    const name = page.getByPlaceholder('Friday evening program');
    await expect(name).toBeVisible();
    if (options.paced) {
      await holdCallout(page, name, 'Name the program', 'right', 700);
      await smoothFill(page, name, rundownName);
    } else {
      await name.fill(rundownName);
    }
    const library = page.locator('details').filter({ hasText: 'Add Library media' }).first();
    const list = library.getByTestId('artifact-picker-library');
    for (const fileName of data.videoNames) {
      // Adding a clip closes this panel. Open it again before the next row.
      if (!(await library.evaluate((node) => (node as HTMLDetailsElement).open))) {
        await library.locator('> summary').click();
      }
      await library.scrollIntoViewIfNeeded();
      const row = list.getByText(fileName, { exact: true }).first();
      await row.scrollIntoViewIfNeeded();
      await expect(row).toBeVisible({ timeout: 15_000 });
      await row.click();
    }
    await expect(page.getByLabel('Planned program duration')).toBeVisible();
    const save = page.getByRole('button', { name: 'Save rundown' });
    if (options.paced) await holdCallout(page, save, 'Save rundown', 'left', 800);
    await save.click();
    await expect(page.getByText(/rundown saved/i)).toBeVisible({ timeout: 15_000 });
  }
  await expect(page.getByLabel('Program order')).toBeVisible();
}
