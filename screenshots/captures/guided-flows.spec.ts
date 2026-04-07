import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { expect, test, type Page } from '@playwright/test';

const __dirname = dirname(fileURLToPath(import.meta.url));

import { createAuthenticatedApi } from '../helpers/auth';
import { cleanupSeededRoutes } from '../helpers/seed';

/**
 * Captures step-by-step guided-flow screenshots for the selfhost user-guide.
 *
 * Each flow produces numbered images:
 *   create-route-1-open.jpg
 *   create-route-2-identity.jpg
 *   create-route-3-source.jpg
 *   create-route-4-created.jpg
 *   add-output-1-workspace.jpg
 *   add-output-2-dialog.jpg
 *   add-output-3-added.jpg
 *
 * These are placed in `docs/src/images/user-guide/flows/` and can be
 * referenced from the mdBook user-guide with step-by-step instructions.
 */

const FLOWS_DIR = resolve(
  __dirname,
  '../../docs/src/images/user-guide/flows',
);
const SEED_PREFIX = 'docs-flow';

// ---------------------------------------------------------------------------
// Setup / teardown
// ---------------------------------------------------------------------------

test.beforeAll(async () => {
  const baseURL = process.env.FLUXOMNI_URL ?? 'http://localhost';
  const api = await createAuthenticatedApi(baseURL);
  try {
    await cleanupSeededRoutes(api, SEED_PREFIX);
  } finally {
    await api.dispose();
  }
});

test.afterAll(async () => {
  const baseURL = process.env.FLUXOMNI_URL ?? 'http://localhost';
  const api = await createAuthenticatedApi(baseURL);
  try {
    await cleanupSeededRoutes(api, SEED_PREFIX);
  } finally {
    await api.dispose();
  }
});

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function waitForAppReady(page: Page) {
  await page.waitForSelector('[data-testid="sidebar"], nav, aside', {
    timeout: 15_000,
  });
  await page.waitForTimeout(1500);
}

function screenshotPath(name: string): string {
  return resolve(FLOWS_DIR, `${name}.jpg`);
}

async function capture(page: Page, name: string) {
  await page.waitForTimeout(600);
  await page.screenshot({
    path: screenshotPath(name),
    type: 'jpeg',
    quality: 90,
  });
}

// ---------------------------------------------------------------------------
// Flow: Create Route
// ---------------------------------------------------------------------------

test.describe('Create Route flow', () => {
  test('step-by-step route creation', async ({ page }) => {
    // Step 1: Navigate to routes list (empty or with existing routes)
    await page.goto('/routes');
    await waitForAppReady(page);
    await capture(page, 'create-route-1-open');

    // Step 2: Click "+ New Route" to open the dialog
    const newRouteButton = page.getByRole('button', { name: /new route/i });
    if (await newRouteButton.isVisible()) {
      await newRouteButton.click();
    } else {
      const createButton = page.getByRole('button', {
        name: /create.*route|add.*route/i,
      });
      await createButton.click();
    }

    await page.waitForSelector(
      '[role="dialog"], .modal, [data-testid="create-route-modal"]',
      { timeout: 10_000 },
    );
    await page.waitForTimeout(800);

    // Step 2: Capture the empty create-route dialog
    await capture(page, 'create-route-2-dialog');

    // Step 3: Fill in route identity
    const labelInput = page.getByLabel(/route label/i).or(
      page.getByPlaceholder(/label|name/i).first(),
    );
    if (await labelInput.isVisible()) {
      await labelInput.fill('Main Broadcast');
    }

    const keyInput = page.getByLabel(/route key/i).or(
      page.getByPlaceholder(/key/i).first(),
    );
    if (await keyInput.isVisible()) {
      await keyInput.fill(`${SEED_PREFIX}-main-broadcast`);
    }
    await capture(page, 'create-route-3-identity');

    // Step 4: Submit the form (scope to within the modal dialog)
    const dialog = page.locator('.modal-open, [role="dialog"]').first();
    const submitButton = dialog
      .getByRole('button', { name: /create route/i })
      .or(dialog.getByRole('button', { name: /^create$/i }))
      .or(dialog.locator('button[type="submit"]'));
    if (await submitButton.first().isVisible()) {
      await submitButton.first().click();
      // Wait for navigation or dialog close
      await page.waitForTimeout(2000);
    }
    await capture(page, 'create-route-4-created');
  });
});

// ---------------------------------------------------------------------------
// Flow: Add Output
// ---------------------------------------------------------------------------

test.describe('Add Output flow', () => {
  test('step-by-step output addition', async ({ page }) => {
    // Navigate to the route workspace — find an existing route first
    await page.goto('/routes');
    await waitForAppReady(page);

    // Click the first workspace link
    const workspaceLink = page
      .getByRole('link', { name: /open workspace/i })
      .first();
    if (await workspaceLink.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await workspaceLink.click();
    } else {
      // If no routes visible, skip this flow gracefully
      test.skip(true, 'No routes available for add-output flow');
      return;
    }
    await waitForAppReady(page);

    // Step 1: Route workspace before adding output
    await capture(page, 'add-output-1-workspace');

    // Step 2: Click "+ Add output"
    const addOutputButton = page
      .getByRole('button', { name: /add output/i })
      .first();

    if (
      await addOutputButton.isVisible({ timeout: 5_000 }).catch(() => false)
    ) {
      await addOutputButton.click();
      await page.waitForTimeout(800);
      await capture(page, 'add-output-2-dialog');

      // Step 3: Fill in output details
      const dstInput = page
        .getByLabel(/destination|url|address/i)
        .or(page.getByPlaceholder(/rtmp:\/\//i).first());
      if (await dstInput.isVisible()) {
        await dstInput.fill('rtmp://a.rtmp.youtube.com/live2/my-stream-key');
      }

      const outputLabel = page
        .getByLabel(/output.*label|label/i)
        .or(page.getByPlaceholder(/label|name/i).first());
      if (await outputLabel.isVisible()) {
        await outputLabel.fill('YouTube Live');
      }

      // Submit
      const submitOutput = page
        .getByRole('button', { name: /add|create|save/i })
        .last();
      if (await submitOutput.isVisible()) {
        await submitOutput.click();
        await page.waitForTimeout(2000);
      }
      await capture(page, 'add-output-3-added');
    } else {
      // Navigate to Routing tab if outputs are in a separate tab
      const routingTab = page.getByRole('tab', { name: /routing/i });
      if (await routingTab.isVisible()) {
        await routingTab.click();
        await page.waitForTimeout(1000);
        await capture(page, 'add-output-1-routing-tab');
      }
    }
  });
});
