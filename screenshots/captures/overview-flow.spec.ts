import { spawn, type ChildProcessWithoutNullStreams } from 'node:child_process';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { expect, test, type Browser, type Locator, type Page } from '@playwright/test';

import { createAuthenticatedApi } from '../helpers/auth';
import { requestGraphql } from '../helpers/graphql';
import { waitForAppReady } from '../helpers/readiness';
import { cleanupSeededRoutes } from '../helpers/seed';
import { saveRecordedVideo } from '../helpers/video';

const __dirname = dirname(fileURLToPath(import.meta.url));

const VIDEOS_DIR = resolve(__dirname, '../../docs/src/videos/user-guide');
const SEED_PREFIX = 'docs-overview-flow';
const ROUTE_LABEL = `Live Overview ${SEED_PREFIX}`;
const OUTPUT_LABEL = 'YouTube Live';

const FIND_ROUTE_BY_LABEL = `
  query FindRouteByLabel {
    routes {
      allRoutes {
        id
        label
        presentation { phase label }
        assignedMediaNode { publicHost rtmpPort }
        publishCredentials { token }
        routeSources {
          sources {
            id
            presentation { phase label }
          }
        }
      }
    }
  }
`;

type ListedRoute = {
  id: string;
  label: string | null;
  presentation: { phase: string; label: string };
  assignedMediaNode: { publicHost: string | null; rtmpPort: number | null } | null;
  publishCredentials: Array<{ token: string | null }>;
  routeSources: {
    sources: Array<{
      id: string;
      presentation: { phase: string; label: string };
    }>;
  };
};

test.describe('Overview video', () => {
  test.describe.configure({ timeout: 180_000 });

  test.beforeAll(async () => {
    const api = await createAuthenticatedApi(process.env.FLUXOMNI_URL ?? 'http://localhost');
    try {
      await cleanupSeededRoutes(api, SEED_PREFIX);
    } finally {
      await api.dispose();
    }
  });

  test.afterAll(async () => {
    const api = await createAuthenticatedApi(process.env.FLUXOMNI_URL ?? 'http://localhost');
    try {
      await cleanupSeededRoutes(api, SEED_PREFIX);
    } finally {
      await api.dispose();
    }
  });

  test('flow-overview.webm — create route, publish RTMP, preview, add output', async ({
    browser,
  }) => {
    await warmAppInBrowser(browser);
    const { context, page } = await createRecordedPage(browser);
    let publisher: ChildProcessWithoutNullStreams | undefined;

    try {
      await page.goto('/routes');
      await waitForAppReady(page);
      await page.waitForTimeout(1200);

      const newRouteButton = getCreateRouteButton(page);
      await holdCallout(page, newRouteButton, 'Create a route', 'left', 900);
      await smoothClick(page, newRouteButton);

      const dialog = page.locator('.modal-open, [role="dialog"]').first();
      await expect(dialog).toBeVisible({ timeout: 10_000 });
      await holdCallout(page, dialog, 'RTMP, SRT, or WebRTC ingest', 'right', 1100);

      const labelInput = page
        .getByTestId('add-input-modal:label-input')
        .or(page.getByLabel(/route label/i))
        .or(page.getByPlaceholder(/label|name/i))
        .first();
      await smoothFill(page, labelInput, ROUTE_LABEL);

      const submitButton = getCreateRouteSubmit(dialog);
      await holdCallout(page, submitButton, 'Save route', 'left', 700);
      await smoothClick(page, submitButton);
      await expect(dialog).toBeHidden({ timeout: 10_000 });

      const routeId = await waitForRouteId(ROUTE_LABEL);
      await selectExpandedView(page);
      const routeCard = page.getByText(ROUTE_LABEL).first();
      await expect(routeCard).toBeVisible({ timeout: 10_000 });
      await holdCallout(page, routeCard, 'Route is armed', 'right', 900);
      await openWorkspaceFromRouteCard(page, routeId);

      await waitForAppReady(page);
      const publishUrl = await waitForPublishUrlFromApi(ROUTE_LABEL);
      const publishTarget = page.locator('main').getByText(/rtmp:\/\//i).first();
      await holdCallout(page, publishTarget, 'Copy publish URL', 'left', 900);

      publisher = startRtmpPublisher(publishUrl);
      await waitForRouteLive(ROUTE_LABEL);
      await page.reload();
      await waitForAppReady(page);
      const liveStatus = page.locator('main').getByText(/^live$/i).first();
      await expect(liveStatus).toBeVisible({ timeout: 20_000 });
      await holdCallout(page, liveStatus, 'Live input detected', 'left', 1200);

      const monitorPanel = page
        .locator('main video:visible, main canvas:visible')
        .or(page.locator('main').getByText(/waiting for stream|unsupported playback/i))
        .first();
      await holdCallout(page, monitorPanel, 'HLS preview', 'left', 1200);

      const addOutputButton = page.getByRole('button', { name: /add output/i }).first();
      await holdCallout(page, addOutputButton, 'Add destination', 'left', 800);
      await smoothClick(page, addOutputButton);

      const outputModal = page.getByRole('heading', {
        name: /add new output destination/i,
      });
      await expect(outputModal).toBeVisible({ timeout: 10_000 });
      await smoothFill(
        page,
        page.getByTestId('add-output-modal:rtmp-input'),
        'rtmp://a.rtmp.youtube.com/live2/demo-stream-key',
      );
      await smoothFill(page, page.getByTestId('add-output-modal:label-input'), OUTPUT_LABEL);
      await holdCallout(
        page,
        page.getByTestId('add-output-modal:confirm'),
        'Send to YouTube',
        'left',
        700,
      );
      await smoothClick(page, page.getByTestId('add-output-modal:confirm'));
      await expect(outputModal).toBeHidden({ timeout: 10_000 });
      const outputRow = page.getByText(OUTPUT_LABEL).first();
      await expect(outputRow).toBeVisible({ timeout: 10_000 });
      await holdCallout(page, outputRow, 'One input, many outputs', 'left', 1400);
      await showPlaylistWorkspace(page);
      await page.waitForTimeout(1000);
    } finally {
      stopPublisher(publisher);
      await saveRecordedVideo(page, context, resolve(VIDEOS_DIR, 'flow-overview.webm'), {
        trimStartSeconds: 3,
      });
    }
  });
});

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

async function waitForRouteId(label: string): Promise<string> {
  const api = await createAuthenticatedApi(process.env.FLUXOMNI_URL ?? 'http://localhost');
  try {
    const deadline = Date.now() + 20_000;
    while (Date.now() < deadline) {
      const route = await findRoute(api, label);
      if (route) return route.id;
      await new Promise((resolveWait) => setTimeout(resolveWait, 500));
    }
  } finally {
    await api.dispose();
  }
  throw new Error(`Route "${label}" was not created`);
}

async function waitForRouteLive(label: string): Promise<void> {
  const api = await createAuthenticatedApi(process.env.FLUXOMNI_URL ?? 'http://localhost');
  try {
    const deadline = Date.now() + 45_000;
    while (Date.now() < deadline) {
      const route = await findRoute(api, label);
      const sourceLive = route?.routeSources.sources.some(
        (source) => source.presentation.phase === 'LIVE',
      );
      if (route?.presentation.phase === 'RUNNING' || sourceLive) return;
      await new Promise((resolveWait) => setTimeout(resolveWait, 1000));
    }
  } finally {
    await api.dispose();
  }
  throw new Error(`Route "${label}" did not become live`);
}

async function findRoute(
  api: Awaited<ReturnType<typeof createAuthenticatedApi>>,
  label: string,
): Promise<ListedRoute | undefined> {
  const data = await requestGraphql<{ routes: { allRoutes: ListedRoute[] } }>(
    api,
    FIND_ROUTE_BY_LABEL,
  );
  return data.routes.allRoutes.find((route) => route.label === label);
}

async function waitForPublishUrlFromApi(label: string): Promise<string> {
  const api = await createAuthenticatedApi(process.env.FLUXOMNI_URL ?? 'http://localhost');
  try {
    const deadline = Date.now() + 45_000;
    while (Date.now() < deadline) {
      const route = await findRoute(api, label);
      const token = route?.publishCredentials.find((credential) => credential.token)?.token;
      const host =
        route?.assignedMediaNode?.publicHost ??
        new URL(process.env.FLUXOMNI_URL ?? 'http://localhost').hostname;
      const port = route?.assignedMediaNode?.rtmpPort ?? 1935;
      if (token && host) {
        return `rtmp://${host}:${port}/live/${token}`;
      }
      await new Promise((resolveWait) => setTimeout(resolveWait, 1000));
    }
  } finally {
    await api.dispose();
  }
  throw new Error(`Could not build an RTMP publish URL for route "${label}"`);
}

function startRtmpPublisher(url: string): ChildProcessWithoutNullStreams {
  const publisher = spawn('ffmpeg', [
    '-hide_banner',
    '-loglevel',
    'error',
    '-re',
    '-f',
    'lavfi',
    '-i',
    'testsrc2=size=1280x720:rate=30',
    '-f',
    'lavfi',
    '-i',
    'sine=frequency=880:sample_rate=48000',
    '-c:v',
    'libx264',
    '-preset',
    'veryfast',
    '-pix_fmt',
    'yuv420p',
    '-g',
    '60',
    '-c:a',
    'aac',
    '-b:a',
    '128k',
    '-f',
    'flv',
    url,
  ]);

  let stopping = false;
  let stderr = '';
  publisher.stderr.on('data', (chunk: Buffer) => {
    stderr += chunk.toString('utf8');
  });
  publisher.once('exit', (code, signal) => {
    if (!stopping && code !== 0 && signal !== 'SIGTERM') {
      console.error(
        `Overview FFmpeg publisher exited with code ${code ?? signal}: ${stderr.trim()}`,
      );
    }
  });
  publisher.once('close', () => {
    stopping = true;
  });
  return publisher;
}

function stopPublisher(publisher: ChildProcessWithoutNullStreams | undefined) {
  if (!publisher || publisher.killed) return;
  publisher.removeAllListeners('exit');
  publisher.kill('SIGTERM');
}

function getCreateRouteButton(page: Page) {
  return page.getByRole('button', { name: /create route|new route/i }).first();
}

function getCreateRouteSubmit(dialog: Locator) {
  return dialog
    .locator('button')
    .filter({ hasText: /create route/i })
    .or(dialog.getByRole('button', { name: /create route|add or edit/i }))
    .or(dialog.locator('button[type="submit"]'))
    .first();
}

async function clickRoutingTab(page: Page) {
  const routingLink = page.getByRole('link', { name: /^Routing$/ }).first();
  if (await routingLink.isVisible().catch(() => false)) {
    await smoothClick(page, routingLink);
    await page.waitForTimeout(700);
    return;
  }

  const routingTab = page.getByRole('tab', { name: /^Routing$/ }).first();
  if (await routingTab.isVisible().catch(() => false)) {
    await smoothClick(page, routingTab);
    await page.waitForTimeout(700);
  }
}

async function openWorkspaceFromRouteCard(page: Page, routeId: string) {
  const routeLink = page
    .locator(`a[href="/routes/${routeId}"], a[href$="/routes/${routeId}"]`)
    .first();
  if (await routeLink.isVisible().catch(() => false)) {
    await holdCallout(page, routeLink, 'Open workspace', 'left', 700);
    await smoothClick(page, routeLink);
    return;
  }

  const workspaceLink = page
    .getByRole('link', { name: /open workspace|workspace/i })
    .or(page.getByRole('button', { name: /open workspace|workspace/i }))
    .first();
  await holdCallout(page, workspaceLink, 'Open workspace', 'left', 700);
  await smoothClick(page, workspaceLink);
}

async function showPlaylistWorkspace(page: Page) {
  const viewSelector = page.locator('button.workspace-mode-trigger').first();

  await expect(viewSelector).toBeVisible({ timeout: 10_000 });

  await holdCallout(page, viewSelector, 'Switch workspace view', 'right', 900);
  await smoothClick(page, viewSelector);

  const playlistOption = page
    .locator('button.workspace-mode-option:has-text("Playlist Playout")')
    .first();

  await expect(playlistOption).toBeVisible({ timeout: 10_000 });
  await holdCallout(page, playlistOption, 'Playlist workspace', 'right', 800);
  await smoothClick(page, playlistOption);
  await page.waitForTimeout(700);
  await scrollPlaylistWorkspace(page);
}

async function scrollPlaylistWorkspace(page: Page) {
  const playlistSurface = page
    .locator('main')
    .getByText(/playlist|queue|from library|import/i)
    .first();

  await expect(playlistSurface).toBeVisible({ timeout: 10_000 });
  await holdCallout(page, playlistSurface, 'Playlist queue', 'right', 900);

  await page.mouse.move(960, 520, { steps: 24 });
  for (const delta of [180, 220, 220, -120]) {
    await page.mouse.wheel(0, delta);
    await page.waitForTimeout(350);
  }
  await page.waitForTimeout(800);
}

async function selectExpandedView(page: Page) {
  const expandedButton = page.getByRole('button', { name: /expanded/i }).first();
  if (await expandedButton.isVisible().catch(() => false)) {
    await smoothClick(page, expandedButton);
    await page.waitForTimeout(500);
  }
}

async function bringIntoView(target: Locator) {
  await target.first().scrollIntoViewIfNeeded({ timeout: 10_000 });
}

async function moveTo(page: Page, target: Locator) {
  await bringIntoView(target);
  const box = await target.first().boundingBox();
  if (!box) return;
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2, {
    steps: 24,
  });
}

async function smoothClick(page: Page, target: Locator) {
  await expect(target.first()).toBeVisible({ timeout: 10_000 });
  await bringIntoView(target);
  await moveTo(page, target);
  await page.waitForTimeout(250);
  await target.first().click();
  await page.waitForTimeout(650);
}

async function smoothFill(page: Page, target: Locator, value: string) {
  await expect(target.first()).toBeVisible({ timeout: 10_000 });
  await bringIntoView(target);
  await moveTo(page, target);
  await page.waitForTimeout(200);
  await target.first().click();
  await page.keyboard.press(process.platform === 'darwin' ? 'Meta+A' : 'Control+A');
  await page.keyboard.type(value, { delay: 30 });
  await page.waitForTimeout(250);
}

async function clearCallouts(page: Page) {
  await page.evaluate(() => {
    document.querySelectorAll('.docs-callout-layer').forEach((node) => {
      node.remove();
    });
  });
}

async function holdCallout(
  page: Page,
  target: Locator,
  label: string,
  side: 'left' | 'right' | 'top' | 'bottom' = 'left',
  duration = 1000,
) {
  await expect(target.first()).toBeVisible({ timeout: 10_000 });
  await bringIntoView(target);
  await addCallout(page, target, label, side);
  await page.waitForTimeout(duration);
  await clearCallouts(page);
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
        bubbleX =
          box.x - bubbleWidth - 28 >= margin
            ? box.x - bubbleWidth - 28
            : box.x + box.width + 28;
      } else if (side === 'right') {
        bubbleX =
          box.x + box.width + 28 + bubbleWidth <= viewportWidth - margin
            ? box.x + box.width + 28
            : box.x - bubbleWidth - 28;
      } else if (side === 'top') {
        bubbleY = box.y - bubbleHeight - 28;
      } else {
        bubbleY = box.y + box.height + 28;
      }

      bubbleX = Math.max(margin, Math.min(viewportWidth - bubbleWidth - margin, bubbleX));
      bubbleY = Math.max(
        margin,
        Math.min(viewportHeight - bubbleHeight - margin, bubbleY),
      );

      const startX =
        bubbleX +
        (bubbleX < box.x ? bubbleWidth : bubbleX > box.x + box.width ? 0 : bubbleWidth / 2);
      const startY =
        bubbleY +
        (side === 'top' ? bubbleHeight : side === 'bottom' ? 0 : bubbleHeight / 2);

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
