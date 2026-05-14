import { expect, type Page } from '@playwright/test';

/**
 * Waits until the Fluxomni Studio shell is fully rendered.
 *
 * Use this before screenshots and before any recorded video action. It checks
 * the sidebar, branding, primary nav, main area, fonts, and stable layout so
 * captures do not start from a blank or half-hydrated page.
 */
export async function waitForAppReady(page: Page) {
  await page.waitForLoadState('domcontentloaded');
  const sidebar = page.locator('[data-testid="sidebar"], aside').first();
  await sidebar.waitFor({ state: 'visible', timeout: 30_000 });
  await expect(sidebar.getByText(/Fluxomni(?: Studio)?/i).first()).toBeVisible({
    timeout: 30_000,
  });
  await expect(sidebar.getByRole('link', { name: /routes/i }).first()).toBeVisible({
    timeout: 30_000,
  });
  await expect(sidebar.getByRole('link', { name: /artifacts/i }).first()).toBeVisible({
    timeout: 30_000,
  });
  await expect(page.locator('main')).toBeVisible({ timeout: 30_000 });
  await page.waitForLoadState('networkidle', { timeout: 10_000 }).catch(() => undefined);
  await waitForStableLayout(page);
}

export async function waitForRouteWorkspaceReady(page: Page) {
  await waitForAppReady(page);
  await expect(page.getByRole('navigation', {
    name: /route workspace sections/i,
  })).toBeVisible({ timeout: 30_000 });
  await expect(page.getByRole('heading', { name: /signal path/i })).toBeVisible({
    timeout: 30_000,
  });
  await expect(page.getByRole('heading', { name: /^queue$/i })).toBeVisible({
    timeout: 30_000,
  });
  await expect(page.getByText(/rtmp:\/\//i).first()).toBeVisible({
    timeout: 30_000,
  });
  await waitForStableLayout(page);
}

export async function waitForStableLayout(page: Page) {
  await page.waitForFunction(
    () => {
      const sidebar = document.querySelector<HTMLElement>(
        '[data-testid="sidebar"], aside',
      );
      const main = document.querySelector<HTMLElement>('main');
      const logo = document.querySelector<HTMLElement>(
        'img[alt="Fluxomni Logo"], img[alt="Fluxomni Studio Logo"]',
      );
      if (!sidebar || !main) return false;
      const sidebarBox = sidebar.getBoundingClientRect();
      const mainBox = main.getBoundingClientRect();
      const logoReady = !logo || logo.getBoundingClientRect().width >= 24;
      return (
        sidebarBox.width >= 240 &&
        sidebarBox.height >= 600 &&
        mainBox.width >= 800 &&
        mainBox.height >= 600 &&
        logoReady &&
        document.fonts?.status !== 'loading'
      );
    },
    undefined,
    { timeout: 30_000 },
  );
}
