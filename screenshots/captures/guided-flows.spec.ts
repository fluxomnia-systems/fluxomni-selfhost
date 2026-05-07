import { mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  expect,
  test,
  type Browser,
  type Locator,
  type Page,
} from '@playwright/test';

const __dirname = dirname(fileURLToPath(import.meta.url));

import { createAuthenticatedApi } from '../helpers/auth';
import { cleanupSeededRoutes, createRoute } from '../helpers/seed';

/**
 * Captures step-by-step guided-flow screenshots for the selfhost user-guide.
 *
 * Each flow produces numbered images:
 *   create-route-1-open.jpg
 *   create-route-2-dialog.jpg
 *   create-route-3-identity.jpg
 *   create-route-4-created.jpg
 *   add-output-1-workspace.jpg
 *   add-output-2-dialog.jpg
 *   add-output-3-added.jpg
 *
 * It also records short WebM walkthroughs:
 *   create-route.webm
 *   add-output.webm
 *
 * These are placed in `docs/src/images/user-guide/flows/` and can be
 * referenced from the mdBook user-guide with step-by-step instructions.
 */

const FLOWS_DIR = resolve(
  __dirname,
  '../../docs/src/images/user-guide/flows',
);
const VIDEOS_DIR = resolve(__dirname, '../../docs/src/videos/user-guide');
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
  await page.waitForLoadState('domcontentloaded');
  await page
    .locator('[data-testid="sidebar"], nav, aside, main')
    .first()
    .waitFor({ state: 'visible', timeout: 30_000 });
  await page.waitForLoadState('load', { timeout: 5000 }).catch(() => undefined);
  await page.waitForFunction(
    () => {
      const logo = document.querySelector<HTMLImageElement>(
        'img[alt="FluxOmni Logo"]',
      );
      const sidebar = document.querySelector<HTMLElement>('aside');
      const main = document.querySelector<HTMLElement>('main');
      if (!main) return false;
      if (!logo || !sidebar) return true;
      return (
        logo.getBoundingClientRect().width < 96 &&
        sidebar.getBoundingClientRect().width < 360
      );
    },
    undefined,
    { timeout: 15_000 },
  );
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

async function clearCallouts(page: Page) {
  await page.evaluate(() => {
    document.querySelectorAll('.docs-callout-layer').forEach((node) => {
      node.remove();
    });
  });
}

async function addCallout(
  page: Page,
  target: Locator,
  label: string,
  side: 'left' | 'right' | 'top' | 'bottom' = 'left',
) {
  await clearCallouts(page);
  const box = await target.first().boundingBox();
  if (!box) return;

  await page.evaluate(
    ({ box, label, side }) => {
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;
      const targetX = box.x + box.width / 2;
      const targetY = box.y + box.height / 2;
      const bubbleWidth = 220;
      const bubbleHeight = 54;
      const margin = 24;
      let bubbleX = targetX - bubbleWidth / 2;
      let bubbleY = targetY - bubbleHeight / 2;

      if (side === 'left') {
        bubbleX = box.x - bubbleWidth - 28;
      } else if (side === 'right') {
        bubbleX = box.x + box.width + 28;
      } else if (side === 'top') {
        bubbleY = box.y - bubbleHeight - 28;
      } else {
        bubbleY = box.y + box.height + 28;
      }

      bubbleX = Math.max(
        margin,
        Math.min(viewportWidth - bubbleWidth - margin, bubbleX),
      );
      bubbleY = Math.max(
        margin,
        Math.min(viewportHeight - bubbleHeight - margin, bubbleY),
      );

      const startX =
        bubbleX +
        (side === 'left'
          ? bubbleWidth
          : side === 'right'
            ? 0
            : bubbleWidth / 2);
      const startY =
        bubbleY +
        (side === 'top'
          ? bubbleHeight
          : side === 'bottom'
            ? 0
            : bubbleHeight / 2);

      const layer = document.createElement('div');
      layer.className = 'docs-callout-layer';
      layer.style.position = 'fixed';
      layer.style.inset = '0';
      layer.style.zIndex = '2147483647';
      layer.style.pointerEvents = 'none';
      layer.style.fontFamily =
        'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';

      layer.innerHTML = `
        <svg width="100%" height="100%" style="position:absolute;inset:0;overflow:visible">
          <defs>
            <marker id="docs-callout-arrow" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto">
              <path d="M 0 0 L 12 6 L 0 12 z" fill="#dc2626"></path>
            </marker>
          </defs>
          <line x1="${startX}" y1="${startY}" x2="${targetX}" y2="${targetY}" stroke="#dc2626" stroke-width="4" marker-end="url(#docs-callout-arrow)" />
          <rect x="${box.x - 4}" y="${box.y - 4}" width="${box.width + 8}" height="${box.height + 8}" rx="10" fill="none" stroke="#dc2626" stroke-width="3" />
        </svg>
        <div style="
          position:absolute;
          left:${bubbleX}px;
          top:${bubbleY}px;
          width:${bubbleWidth}px;
          min-height:${bubbleHeight}px;
          box-sizing:border-box;
          padding:10px 14px;
          border-radius:14px;
          color:white;
          background:#b91c1c;
          box-shadow:0 14px 34px rgba(15, 23, 42, 0.26);
          font-size:15px;
          font-weight:800;
          line-height:1.15;
        ">${label}</div>
      `;
      document.body.appendChild(layer);
    },
    { box, label, side },
  );
}

async function captureWithCallout(
  page: Page,
  name: string,
  target: Locator,
  label: string,
  side: 'left' | 'right' | 'top' | 'bottom' = 'left',
) {
  await addCallout(page, target, label, side);
  await capture(page, name);
  await clearCallouts(page);
}

async function holdCallout(
  page: Page,
  target: Locator,
  label: string,
  side: 'left' | 'right' | 'top' | 'bottom' = 'left',
  duration = 1000,
) {
  await addCallout(page, target, label, side);
  await page.waitForTimeout(duration);
  await clearCallouts(page);
}

async function clickRoutingTab(page: Page) {
  const routingLink = page.getByRole('link', { name: /^Routing$/ }).first();
  if (await routingLink.isVisible().catch(() => false)) {
    await routingLink.click();
    await page.waitForTimeout(800);
    return;
  }

  const routingTab = page.getByRole('tab', { name: /^Routing$/ }).first();
  if (await routingTab.isVisible().catch(() => false)) {
    await routingTab.click();
    await page.waitForTimeout(800);
  }
}

async function selectExpandedView(page: Page) {
  const expandedButton = page.getByRole('button', { name: /expanded/i }).first();
  if (await expandedButton.isVisible().catch(() => false)) {
    await expandedButton.click();
    await page.waitForTimeout(800);
  }
}

function getCreateRouteButton(page: Page) {
  return page
    .getByRole('button', { name: /create route|new route/i })
    .first();
}

function getCreateRouteSubmit(dialog: Locator) {
  return dialog
    .locator('button')
    .filter({ hasText: /create route/i })
    .or(dialog.getByRole('button', { name: /create route|add or edit/i }))
    .or(dialog.locator('button[type="submit"]'))
    .first();
}

async function fillCreateRouteDialog(page: Page) {
  const labelInput = page
    .getByTestId('add-input-modal:label-input')
    .or(page.getByLabel(/route label/i))
    .or(page.getByPlaceholder(/label|name/i))
    .first();
  if (await labelInput.isVisible()) {
    await labelInput.fill(`Main Broadcast ${SEED_PREFIX}`);
  }

  const keyInput = page
    .getByLabel(/route key/i)
    .or(page.getByPlaceholder(/key/i))
    .first();
  if (await keyInput.isVisible()) {
    await keyInput.fill(`${SEED_PREFIX}-main-broadcast`);
  }

  return { labelInput, keyInput };
}

async function createRecordedPage(browser: Browser) {
  const context = await browser.newContext({
    baseURL: process.env.FLUXOMNI_URL ?? 'http://localhost',
    storageState: resolve(__dirname, '../auth-state.json'),
    viewport: { width: 1280, height: 720 },
    recordVideo: {
      dir: test.info().outputPath('videos'),
      size: { width: 1280, height: 720 },
    },
  });
  const page = await context.newPage();
  return { context, page };
}

async function warmAppInBrowser(browser: Browser) {
  const context = await browser.newContext({
    baseURL: process.env.FLUXOMNI_URL ?? 'http://localhost',
    storageState: resolve(__dirname, '../auth-state.json'),
    viewport: { width: 1280, height: 720 },
  });
  const page = await context.newPage();
  await page.goto('/routes');
  await waitForAppReady(page);
  await context.close();
}

async function saveRecordedVideo(
  page: Page,
  context: Awaited<ReturnType<Browser['newContext']>>,
  name: string,
) {
  mkdirSync(VIDEOS_DIR, { recursive: true });
  const video = page.video();
  await context.close();
  const outputPath = resolve(VIDEOS_DIR, `${name}.webm`);
  if (!video) return;
  await video.saveAs(outputPath);
}

async function prepareRoutesMainForVideo(page: Page) {
  await page.goto('/routes');
  await waitForAppReady(page);
  await page.waitForTimeout(1600);
}

async function moveTo(page: Page, target: Locator) {
  const box = await target.first().boundingBox();
  if (!box) return;
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2, {
    steps: 24,
  });
}

async function smoothClick(page: Page, target: Locator) {
  await expect(target.first()).toBeVisible({ timeout: 10_000 });
  await moveTo(page, target);
  await page.waitForTimeout(350);
  await target.first().click();
  await page.waitForTimeout(700);
}

async function smoothFill(page: Page, target: Locator, value: string) {
  await expect(target.first()).toBeVisible({ timeout: 10_000 });
  await moveTo(page, target);
  await page.waitForTimeout(250);
  await target.first().click();
  await page.keyboard.press(process.platform === 'darwin' ? 'Meta+A' : 'Control+A');
  await page.keyboard.type(value, { delay: 45 });
  await page.waitForTimeout(350);
}

async function openWorkspaceFromRoutesMain(page: Page, routeLabel: string) {
  await selectExpandedView(page);
  const routeCard = page.getByText(routeLabel).first();
  await routeCard.waitFor({ timeout: 10_000 });
  const workspaceLink = page
    .getByRole('link', { name: /open workspace/i })
    .or(page.getByRole('button', { name: /open workspace/i }))
    .first();
  await smoothClick(page, workspaceLink);
  await waitForAppReady(page);
}

async function enterWorkspaceAfterMainHold(page: Page, routeId: string) {
  await page.waitForTimeout(1200);
  await page.goto(`/routes/${routeId}`);
  await waitForAppReady(page);
}

async function openWorkspaceFromRoutesLink(page: Page, routeId: string) {
  const workspaceLink = page
    .locator(`a[href="/routes/${routeId}"], a[href$="/routes/${routeId}"]`)
    .first();
  await smoothClick(page, workspaceLink);
  await waitForAppReady(page);
}

// ---------------------------------------------------------------------------
// Flow: Create Route
// ---------------------------------------------------------------------------

test.describe('Create Route flow', () => {
  test('step-by-step route creation', async ({ page }) => {
    // Step 1: Navigate to routes list (empty or with existing routes)
    await page.goto('/routes');
    await waitForAppReady(page);
    const newRouteButton = getCreateRouteButton(page);
    await expect(newRouteButton).toBeVisible({ timeout: 10_000 });
    await captureWithCallout(
      page,
      'create-route-1-open',
      newRouteButton,
      'Click + New Route',
      'left',
    );

    // Step 2: Click "+ New Route" to open the dialog
    await newRouteButton.click();

    await page.waitForSelector(
      '[role="dialog"], .modal, [data-testid="create-route-modal"]',
      { timeout: 10_000 },
    );
    await page.waitForTimeout(800);

    // Step 2: Capture the empty create-route dialog
    const labelInput = page
      .getByTestId('add-input-modal:label-input')
      .or(page.getByLabel(/route label/i))
      .or(page.getByPlaceholder(/label|name/i))
      .first();
    await captureWithCallout(
      page,
      'create-route-2-dialog',
      labelInput,
      'Name the route',
      'right',
    );

    // Step 3: Fill in route identity
    await fillCreateRouteDialog(page);
    const dialog = page.locator('.modal-open, [role="dialog"]').first();
    const submitButton = getCreateRouteSubmit(dialog);
    await captureWithCallout(
      page,
      'create-route-3-identity',
      submitButton,
      'Submit Create route',
      'left',
    );

    // Step 4: Submit the form and show the created route in expanded view.
    if (await submitButton.first().isVisible()) {
      await submitButton.first().click();
      // Wait for navigation or dialog close
      await page.waitForTimeout(2000);
    }
    await selectExpandedView(page);
    const routeCard = page.getByText(`Main Broadcast ${SEED_PREFIX}`).first();
    await routeCard.waitFor({ timeout: 10_000 });
    await captureWithCallout(
      page,
      'create-route-4-created',
      routeCard,
      'Created route in Expanded view',
      'right',
    );
  });
});

// ---------------------------------------------------------------------------
// Flow: Add Output
// ---------------------------------------------------------------------------

test.describe('Add Output flow', () => {
  test('step-by-step output addition', async ({ page }) => {
    const baseURL = process.env.FLUXOMNI_URL ?? 'http://localhost';
    const api = await createAuthenticatedApi(baseURL);

    let routeId: string;
    try {
      const route = await createRoute(api, {
        key: `${SEED_PREFIX}-output-demo`,
        label: `Output Demo ${SEED_PREFIX}`,
      });
      routeId = route.id;
    } finally {
      await api.dispose();
    }

    await page.goto(`/routes/${routeId}`);
    await waitForAppReady(page);

    await clickRoutingTab(page);

    // Step 1: Route workspace with the Routing tab ready for output management
    const addOutputButton = page
      .getByRole('button', { name: /add output/i })
      .first();
    await expect(addOutputButton).toBeVisible({ timeout: 10_000 });
    await captureWithCallout(
      page,
      'add-output-1-workspace',
      addOutputButton,
      'Click + Add output',
      'left',
    );

    // Step 2: Click "+ Add output"
    await addOutputButton.click();
    await page.waitForTimeout(800);
    const dstInput = page.getByTestId('add-output-modal:rtmp-input');
    await captureWithCallout(
      page,
      'add-output-2-dialog',
      dstInput,
      'Paste destination URL',
      'right',
    );

    // Step 3: Fill in output details
    await expect(dstInput).toBeVisible();
    await dstInput.fill('rtmp://a.rtmp.youtube.com/live2/my-stream-key');

    const outputLabel = page.getByTestId('add-output-modal:label-input');
    await expect(outputLabel).toBeVisible();
    await outputLabel.fill('YouTube Live');

    // Submit
    const submitOutput = page.getByTestId('add-output-modal:confirm');
    await expect(submitOutput).toBeVisible();
    await submitOutput.click();
    await page.waitForTimeout(2_000);
    const outputRow = page.getByText('YouTube Live').first();
    await outputRow.waitFor({ timeout: 10_000 });
    await captureWithCallout(
      page,
      'add-output-3-added',
      outputRow,
      'Output is now connected',
      'right',
    );
  });
});

// ---------------------------------------------------------------------------
// Videos
// ---------------------------------------------------------------------------

test.describe('Guided videos', () => {
  test.describe.configure({ timeout: 120_000 });

  test('create-route.webm — Route creation interaction', async ({ browser }) => {
    await warmAppInBrowser(browser);
    const { context, page } = await createRecordedPage(browser);
    await prepareRoutesMainForVideo(page);

    const newRouteButton = getCreateRouteButton(page);
    await holdCallout(page, newRouteButton, 'Create a route', 'left');
    await smoothClick(page, newRouteButton);
    await expect(page.getByRole('heading', { name: /create route/i })).toBeVisible();

    const labelInput = page
      .getByTestId('add-input-modal:label-input')
      .or(page.getByLabel(/route label/i))
      .or(page.getByPlaceholder(/label|name/i))
      .first();
    await holdCallout(page, labelInput, 'Name the route', 'right');
    await smoothFill(page, labelInput, `Main Broadcast ${SEED_PREFIX}`);

    await page.waitForTimeout(800);
    const dialog = page.locator('.modal-open, [role="dialog"]').first();
    const submitButton = getCreateRouteSubmit(dialog);
    await holdCallout(page, submitButton, 'Save route', 'left');
    await smoothClick(page, submitButton);
    await expect(dialog).toBeHidden({ timeout: 10_000 });
    await selectExpandedView(page);
    const routeLabel = page.getByText(`Main Broadcast ${SEED_PREFIX}`).first();
    await expect(routeLabel).toBeVisible({
      timeout: 10_000,
    });
    await holdCallout(page, routeLabel, 'Route is ready', 'right', 1400);
    await page.waitForTimeout(1600);
    await saveRecordedVideo(page, context, 'create-route');
  });

  test('add-output.webm — Output addition interaction', async ({ browser }) => {
    await warmAppInBrowser(browser);
    const baseURL = process.env.FLUXOMNI_URL ?? 'http://localhost';
    const api = await createAuthenticatedApi(baseURL);

    let routeId: string;
    try {
      const route = await createRoute(api, {
        key: `${SEED_PREFIX}-output-video`,
        label: `Output Video ${SEED_PREFIX}`,
      });
      routeId = route.id;
    } finally {
      await api.dispose();
    }

    const { context, page } = await createRecordedPage(browser);
    await prepareRoutesMainForVideo(page);
    await selectExpandedView(page);
    const routeLabel = page.getByText(`Output Video ${SEED_PREFIX}`).first();
    await expect(routeLabel).toBeVisible({ timeout: 10_000 });
    await holdCallout(page, routeLabel, 'Open the route workspace', 'right');
    await openWorkspaceFromRoutesLink(page, routeId);
    await clickRoutingTab(page);
    await page.waitForTimeout(800);
    const addOutputButton = page.getByRole('button', { name: /add output/i }).first();
    await holdCallout(page, addOutputButton, 'Add an output', 'left');
    await smoothClick(page, addOutputButton);
    const outputModalHeading = page.getByRole('heading', {
      name: /add new output destination/i,
    });
    await expect(outputModalHeading).toBeVisible({ timeout: 10_000 });
    await expect(page.getByTestId('add-output-modal:rtmp-input')).toBeVisible({
      timeout: 10_000,
    });
    await page.waitForTimeout(900);
    await holdCallout(
      page,
      page.getByTestId('add-output-modal:rtmp-input'),
      'Paste destination URL',
      'right',
    );
    await smoothFill(
      page,
      page.getByTestId('add-output-modal:rtmp-input'),
      'rtmp://a.rtmp.youtube.com/live2/my-stream-key',
    );
    await smoothFill(
      page,
      page.getByTestId('add-output-modal:label-input'),
      'YouTube Live',
    );
    await page.waitForTimeout(800);
    const confirmButton = page.getByTestId('add-output-modal:confirm');
    await holdCallout(page, confirmButton, 'Save output', 'left');
    await smoothClick(page, confirmButton);
    await expect(outputModalHeading).toBeHidden({ timeout: 10_000 });
    const outputLabel = page.getByText('YouTube Live').first();
    await expect(outputLabel).toBeVisible({
      timeout: 10_000,
    });
    await holdCallout(page, outputLabel, 'Output connected', 'left', 1400);
    await page.waitForTimeout(1600);
    await saveRecordedVideo(page, context, 'add-output');
  });
});
