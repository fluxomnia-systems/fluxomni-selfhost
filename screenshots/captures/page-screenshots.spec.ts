import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { test, type Page } from '@playwright/test';

const __dirname = dirname(fileURLToPath(import.meta.url));

import { createAuthenticatedApi } from '../helpers/auth';
import {
  cleanupSeededRoutes,
  seedRoutesListScenario,
  type SeededRoute,
} from '../helpers/seed';

/**
 * Captures page-level screenshots used in the selfhost user-guide
 * documentation. Each screenshot replaces one image file under
 * `docs/src/images/user-guide/`.
 *
 * Screenshots:
 *   routes-list.jpg         — Routes list page           (user-guide/overview.md)
 *   create-route.jpg        — Create Route dialog         (user-guide/routes.md)
 *   route-workspace.jpg     — Route workspace              (user-guide/routes.md)
 *   route-routing.jpg       — Route Routing tab            (user-guide/routes.md)
 *   route-edit-advanced.jpg — Edit Route advanced routing   (user-guide/routes.md)
 *   attention.jpg           — Attention page                (user-guide/routes.md)
 *   fleet.jpg               — Fleet page                   (user-guide/fleet.md)
 *   settings.jpg            — Settings page                (user-guide/settings.md)
 *   settings-security.jpg   — Settings Security section    (user-guide/settings.md)
 *   settings-users.jpg      — Settings Users section       (user-guide/settings.md)
 *   login.jpg               — Sign-in page                 (user-guide/settings.md)
 */

const IMAGES_DIR = resolve(__dirname, '../../docs/src/images/user-guide');
const SEED_PREFIX = 'docs-screenshot';

let seededRoutes: SeededRoute[] = [];

test.beforeAll(async () => {
  const baseURL = process.env.FLUXOMNI_URL ?? 'http://localhost';
  const api = await createAuthenticatedApi(baseURL);

  try {
    await cleanupSeededRoutes(api, SEED_PREFIX);
    seededRoutes = await seedRoutesListScenario(api, SEED_PREFIX);
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
// Wait helpers
// ---------------------------------------------------------------------------

/** Waits for the main content area to be present and stable. */
async function waitForAppReady(page: Page) {
  // Wait for the sidebar to be visible (app is hydrated)
  await page.waitForSelector('[data-testid="sidebar"], nav, aside', {
    timeout: 15_000,
  });
  // Brief settle for any animations or subscription connections
  await page.waitForTimeout(1500);
}

// ---------------------------------------------------------------------------
// Captures
// ---------------------------------------------------------------------------

test('routes-list.jpg — Routes list page', async ({ page }) => {
  await page.goto('/');
  await waitForAppReady(page);
  // Navigate to routes if not already there
  await page.goto('/routes');
  await waitForAppReady(page);
  await page.screenshot({
    path: resolve(IMAGES_DIR, 'routes-list.jpg'),
    type: 'jpeg',
    quality: 90,
  });
});

test('create-route.jpg — Create Route dialog', async ({ page }) => {
  await page.goto('/routes');
  await waitForAppReady(page);

  // Click the "+ New Route" button to open the create-route dialog
  const newRouteButton = page.getByRole('button', { name: /new route/i });
  if (await newRouteButton.isVisible()) {
    await newRouteButton.click();
  } else {
    // Fallback: look for a "Create Route" or "+" button
    const createButton = page.getByRole('button', {
      name: /create.*route|add.*route/i,
    });
    await createButton.click();
  }

  // Wait for the modal/dialog to appear
  await page.waitForSelector('[role="dialog"], .modal, [data-testid="create-route-modal"]', {
    timeout: 10_000,
  });
  await page.waitForTimeout(800);

  await page.screenshot({
    path: resolve(IMAGES_DIR, 'create-route.jpg'),
    type: 'jpeg',
    quality: 90,
  });

  // Close the dialog so it does not interfere with subsequent captures
  await page.keyboard.press('Escape');
  await page.waitForTimeout(500);
});

test('route-workspace.jpg — Route workspace', async ({ page }) => {
  // Open the first seeded route's workspace
  const routeId = seededRoutes[0]?.id;
  if (routeId) {
    await page.goto(`/routes/${routeId}`);
  } else {
    // Fallback: navigate to routes and click the first one
    await page.goto('/routes');
    await waitForAppReady(page);
    const workspaceLink = page.getByRole('link', { name: /open workspace/i }).first();
    await workspaceLink.click();
  }
  await waitForAppReady(page);

  await page.screenshot({
    path: resolve(IMAGES_DIR, 'route-workspace.jpg'),
    type: 'jpeg',
    quality: 90,
  });
});

test('attention.jpg — Attention page', async ({ page }) => {
  await page.goto('/attention');
  await waitForAppReady(page);

  await page.screenshot({
    path: resolve(IMAGES_DIR, 'attention.jpg'),
    type: 'jpeg',
    quality: 90,
  });
});

test('fleet.jpg — Fleet page', async ({ page }) => {
  await page.goto('/fleet');
  await waitForAppReady(page);

  await page.screenshot({
    path: resolve(IMAGES_DIR, 'fleet.jpg'),
    type: 'jpeg',
    quality: 90,
  });
});

test('settings.jpg — Settings page', async ({ page }) => {
  await page.goto('/settings');
  await waitForAppReady(page);

  await page.screenshot({
    path: resolve(IMAGES_DIR, 'settings.jpg'),
    type: 'jpeg',
    quality: 90,
  });
});

test('settings-security.jpg — Settings Security section', async ({ page }) => {
  await page.goto('/settings/security');
  await waitForAppReady(page);

  await page.screenshot({
    path: resolve(IMAGES_DIR, 'settings-security.jpg'),
    type: 'jpeg',
    quality: 90,
  });
});

test('settings-users.jpg — Settings Users section', async ({ page }) => {
  await page.goto('/settings/users');
  await waitForAppReady(page);

  await page.screenshot({
    path: resolve(IMAGES_DIR, 'settings-users.jpg'),
    type: 'jpeg',
    quality: 90,
  });
});

test('route-routing.jpg — Route Routing tab', async ({ page }) => {
  const routeId = seededRoutes[0]?.id;
  if (routeId) {
    await page.goto(`/routes/${routeId}`);
  } else {
    await page.goto('/routes');
    await waitForAppReady(page);
    const workspaceLink = page.getByRole('link', { name: /open workspace/i }).first();
    await workspaceLink.click();
  }
  await waitForAppReady(page);

  // Click the Routing tab link
  const routingTab = page.getByRole('link', { name: 'Routing' });
  if (await routingTab.isVisible()) {
    await routingTab.click();
    await page.waitForTimeout(800);
  }

  await page.screenshot({
    path: resolve(IMAGES_DIR, 'route-routing.jpg'),
    type: 'jpeg',
    quality: 90,
  });
});

test('route-edit-advanced.jpg — Edit Route advanced routing', async ({ page }) => {
  const routeId = seededRoutes[0]?.id;
  if (routeId) {
    await page.goto(`/routes/${routeId}`);
  } else {
    await page.goto('/routes');
    await waitForAppReady(page);
    const workspaceLink = page.getByRole('link', { name: /open workspace/i }).first();
    await workspaceLink.click();
  }
  await waitForAppReady(page);

  // Click "Edit route" button
  const editButton = page.getByRole('button', { name: /edit route/i });
  if (await editButton.isVisible()) {
    await editButton.click();
    await page.waitForSelector(
      '[role="dialog"], .modal, [data-testid="edit-route-modal"]',
      { timeout: 10_000 },
    );
    await page.waitForTimeout(800);

    // Expand "Advanced routing" section
    const advancedToggle = page.getByText(/advanced routing/i);
    if (await advancedToggle.isVisible()) {
      // Look for a Show/expand trigger near the advanced routing heading
      const showButton = page.getByText('Show', { exact: true }).first();
      if (await showButton.isVisible()) {
        await showButton.click();
        await page.waitForTimeout(600);
      }
    }

    // Scroll dialog to show advanced routing options
    const dialog = page.locator('[role="dialog"], .modal').first();
    await dialog.evaluate((el) => el.scrollTo(0, el.scrollHeight));
    await page.waitForTimeout(600);
  }

  await page.screenshot({
    path: resolve(IMAGES_DIR, 'route-edit-advanced.jpg'),
    type: 'jpeg',
    quality: 90,
  });

  // Close the dialog
  await page.keyboard.press('Escape');
  await page.waitForTimeout(500);
});
