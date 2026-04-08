import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { chromium, type FullConfig } from '@playwright/test';

const __dirname = dirname(fileURLToPath(import.meta.url));
const IMAGES_DIR = resolve(__dirname, '../../docs/src/images/user-guide');

/**
 * Global setup: logs in via the browser and persists storage state so that
 * all test specs share an authenticated browser context.
 */
export default async function globalSetup(_config: FullConfig) {
  const baseURL = process.env.FLUXOMNI_URL ?? 'http://localhost';
  const username = process.env.FLUXOMNI_ADMIN_USER ?? 'admin';
  const password = process.env.FLUXOMNI_ADMIN_PASSWORD ?? '';

  // Check whether auth is required
  const res = await fetch(`${baseURL}/api/auth/status`);
  if (!res.ok) {
    throw new Error(`Cannot reach FluxOmni at ${baseURL} (status ${res.status})`);
  }
  const status = (await res.json()) as { authRequired: boolean };

  if (!status.authRequired) {
    // No auth needed — write empty storage state so Playwright doesn't error
    const { writeFileSync } = await import('node:fs');
    writeFileSync('./auth-state.json', JSON.stringify({ cookies: [], origins: [] }));
    return;
  }

  if (!password) {
    throw new Error(
      'FluxOmni auth is enabled — set FLUXOMNI_ADMIN_PASSWORD before capturing screenshots',
    );
  }

  const browser = await chromium.launch();
  const context = await browser.newContext({ baseURL });
  const page = await context.newPage();

  await page.goto('/');
  // Wait for login form
  await page.waitForSelector('input[type="password"], input[name="password"]', {
    timeout: 15_000,
  });

  // Capture the login page screenshot before filling credentials
  await page.screenshot({
    path: resolve(IMAGES_DIR, 'login.jpg'),
    type: 'jpeg',
    quality: 90,
  });

  // Fill credentials
  const usernameInput = page.locator(
    'input[name="username"], input[type="text"]',
  ).first();
  if (await usernameInput.isVisible()) {
    await usernameInput.fill(username);
  }
  await page.locator('input[type="password"], input[name="password"]').first().fill(password);

  // Submit
  await page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign in")').first().click();

  // Wait for the app to load after login (sidebar appears)
  await page.waitForSelector('[data-testid="sidebar"], nav, aside', {
    timeout: 30_000,
  });

  // Save storage state
  await context.storageState({ path: './auth-state.json' });
  await browser.close();
}
