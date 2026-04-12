import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

import { chromium } from 'playwright';

const __dirname = dirname(fileURLToPath(import.meta.url));
const BASE = process.env.FLUXOMNI_URL ?? 'http://localhost:8080';
const OUT = resolve(__dirname, '../docs/src/images/user-guide');

const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const page = await ctx.newPage();

async function waitForApp() {
  await page.waitForSelector('[data-testid="sidebar"], nav, aside', { timeout: 15000 });
  await page.waitForTimeout(1500);
}

async function capture(name) {
  await page.screenshot({ path: `${OUT}/${name}`, type: 'jpeg', quality: 90 });
  console.log(`  ✓ ${name}`);
}

// 1. Routes list
console.log('Capturing page screenshots...');
await page.goto(`${BASE}/routes`, { waitUntil: 'networkidle' });
await waitForApp();
await capture('routes-list.jpg');

// 2. Create Route dialog
const newRouteBtn = page.getByRole('button', { name: /new route/i });
if (await newRouteBtn.isVisible()) {
  await newRouteBtn.click();
} else {
  await page.getByRole('button', { name: /create.*route|add.*route/i }).click();
}
await page.waitForSelector('[role="dialog"], .modal, [data-testid="create-route-modal"]', { timeout: 10000 });
await page.waitForTimeout(800);
await capture('create-route.jpg');
await page.keyboard.press('Escape');
await page.waitForTimeout(500);

// 3. Route workspace — click the first route
await page.goto(`${BASE}/routes`, { waitUntil: 'networkidle' });
await waitForApp();
// Find and click the first route link to get into workspace
const routeLink = page.locator('a[href*="/routes/"]').first();
if (await routeLink.isVisible({ timeout: 5000 }).catch(() => false)) {
  const href = await routeLink.getAttribute('href');
  await page.goto(`${BASE}${href}`, { waitUntil: 'networkidle' });
  await waitForApp();
}
await capture('route-workspace.jpg');

// 4. Route routing tab
const routingTab = page.getByRole('link', { name: 'Routing' });
if (await routingTab.isVisible({ timeout: 3000 }).catch(() => false)) {
  await routingTab.click();
  await page.waitForTimeout(800);
}
await capture('route-routing.jpg');

// 5. Route edit advanced — go back to workspace and click Edit
await page.goBack();
await waitForApp();
const editBtn = page.getByRole('button', { name: /edit route/i });
if (await editBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
  await editBtn.click();
  await page.waitForSelector('[role="dialog"], .modal', { timeout: 10000 });
  await page.waitForTimeout(800);
  const advancedToggle = page.getByText(/advanced routing/i);
  if (await advancedToggle.isVisible({ timeout: 3000 }).catch(() => false)) {
    const showBtn = page.getByText('Show', { exact: true }).first();
    if (await showBtn.isVisible()) {
      await showBtn.click();
      await page.waitForTimeout(600);
    }
  }
  const dialog = page.locator('[role="dialog"], .modal').first();
  await dialog.evaluate((el) => el.scrollTo(0, el.scrollHeight));
  await page.waitForTimeout(600);
}
await capture('route-edit-advanced.jpg');
await page.keyboard.press('Escape');
await page.waitForTimeout(500);

// 6. Attention page
await page.goto(`${BASE}/attention`, { waitUntil: 'networkidle' });
await waitForApp();
await capture('attention.jpg');

// 7. Fleet page
await page.goto(`${BASE}/fleet`, { waitUntil: 'networkidle' });
await waitForApp();
await capture('fleet.jpg');

// 8. Settings page
await page.goto(`${BASE}/settings`, { waitUntil: 'networkidle' });
await waitForApp();
await capture('settings.jpg');

// 9. Settings security
await page.goto(`${BASE}/settings/security`, { waitUntil: 'networkidle' });
await waitForApp();
await capture('settings-security.jpg');

// 10. Settings users
await page.goto(`${BASE}/settings/users`, { waitUntil: 'networkidle' });
await waitForApp();
await capture('settings-users.jpg');

// 11. Login page — sign out first
const signOutLink = page.getByText('Sign out');
if (await signOutLink.isVisible({ timeout: 3000 }).catch(() => false)) {
  await signOutLink.click();
  await page.waitForTimeout(2000);
}
await page.goto(`${BASE}/`, { waitUntil: 'networkidle' });
await page.waitForTimeout(2000);
await capture('login.jpg');

await browser.close();
console.log('Done — all screenshots captured.');
