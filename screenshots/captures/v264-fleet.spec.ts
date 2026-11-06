import { expect, test, type Page } from '@playwright/test';

import { createAuthenticatedApi } from '../helpers/auth';
import { gateCapture, skipIfCaptureUnavailable } from '../helpers/instance';
import { redactLabSecrets } from '../helpers/redact';
import { waitForAppReady } from '../helpers/readiness';
import { captureStill } from '../helpers/v264-ui';
import { listFleetNodeIds, probeV264Api } from '../helpers/v264-seed';

/**
 * Fleet capacity ceilings, preparation utilization, and private enrollment.
 * Limits are not saved. "Generate join command" is never clicked, and any
 * command, code, private key, or Tailscale host is redacted before the still.
 */

gateCapture();

let node: { id: string; name: string } | undefined;

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
        'This instance is older than v26.4.0. Regenerate Fleet captures against Fluxomni v26.4.0.',
      );
      throw error;
    }
    const nodes = await listFleetNodeIds(api);
    node = nodes[0];
  } finally {
    await api.dispose();
  }
});

test('fleet-control.jpg — control connection beside media access', async ({ page }) => {
  await page.goto('/fleet');
  await waitForAppReady(page);
  const control = page.getByText('Control connection', { exact: true }).first();
  if (!(await control.isVisible().catch(() => false))) {
    const target = requiredNode();
    await page.goto(`/fleet/${encodeURIComponent(target.id)}`);
    await waitForAppReady(page);
  }
  await expect(page.getByText('Control connection', { exact: true }).first()).toBeVisible({
    timeout: 15_000,
  });
  await captureStill(page, 'fleet-control');
});

test('fleet-capacity.jpg — route and output ceilings, not saved', async ({ page }) => {
  await openNode(page);
  const routeLimit = page.getByLabel('Route limit');
  await expect(routeLimit).toBeVisible({ timeout: 15_000 });
  const saveLimits = page.getByRole('button', { name: /save limits/i });
  await expect(saveLimits).toBeVisible();
  await saveLimits.scrollIntoViewIfNeeded();
  await expect(page.getByLabel('Output limit')).toBeVisible();
  await expect(page.getByText(/routes reserved/i).first()).toBeVisible();
  await captureStill(page, 'fleet-capacity');
});

test('fleet-preparation.jpg — preparation limits and waiting work', async ({ page }) => {
  await openNode(page);
  const section = page.getByLabel('Preparation resources');
  if (!(await section.isVisible().catch(() => false))) {
    test.info().annotations.push({
      type: 'gap',
      description:
        'This media node did not show preparation resources. The panel appears when the node reports a preparation budget.',
    });
    test.skip(true, 'Preparation resources are not visible on the selected node.');
  }
  const queue = section.getByText('Preparation queue');
  if (!(await queue.isVisible().catch(() => false))) {
    test.info().annotations.push({
      type: 'gap',
      description:
        'Preparation resources are visible, but hard limits are not configured. CPU, memory, task, and queue figures stay hidden. Limits were not saved.',
    });
    test.skip(true, 'Preparation queue figures are hidden until hard limits are configured.');
  }
  await section.scrollIntoViewIfNeeded();
  await expect(queue).toBeVisible();
  await captureStill(page, 'fleet-preparation');
});

test('fleet-enroll.jpg — private enrollment form with secrets redacted', async ({ page }) => {
  await page.goto('/fleet');
  await waitForAppReady(page);
  await page.getByTestId('fleet-add-node').click();
  const enrollUrl = page.locator('#fleet-onboarding-enrollment-url');
  await expect(enrollUrl).toBeVisible({ timeout: 15_000 });
  await expect(page.getByRole('button', { name: 'Generate join command' })).toBeVisible();
  await redactLabSecrets(page);
  const secret =
    /-----BEGIN [A-Z ]*PRIVATE KEY-----|pk_[A-Za-z0-9]{8,}|\b100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3}\b|\.ts\.net\b/i;
  const visible = await page.locator('body').innerText();
  const fieldValues = await page.locator('input, textarea').evaluateAll((nodes) =>
    nodes.map((node) => (node as HTMLInputElement).value),
  );
  expect(`${visible}\n${fieldValues.join('\n')}`).not.toMatch(secret);
  await captureStill(page, 'fleet-enroll');
  await page.keyboard.press('Escape');
});

function requiredNode(): { id: string; name: string } {
  if (!node) {
    test.skip(true, 'No media node is registered, so Fleet ceilings cannot be captured.');
    throw new Error('No media node is registered.');
  }
  return node;
}

async function openNode(page: Page) {
  const target = requiredNode();
  await page.goto(`/fleet/${encodeURIComponent(target.id)}`);
  await waitForAppReady(page);
}
