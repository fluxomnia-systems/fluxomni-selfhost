import { defineConfig } from '@playwright/test';

/**
 * Screenshot capture configuration for FluxOmni selfhost user-guide docs.
 *
 * Environment variables:
 *   FLUXOMNI_URL           — base URL of the running instance (default: http://localhost)
 *   FLUXOMNI_ADMIN_USER    — admin username (default: admin)
 *   FLUXOMNI_ADMIN_PASSWORD — admin password (required when auth is enabled)
 */
export default defineConfig({
  globalSetup: './helpers/global-setup.ts',
  testDir: './captures',
  fullyParallel: false,
  forbidOnly: true,
  retries: 0,
  workers: 1,
  reporter: [['list']],
  use: {
    baseURL: process.env.FLUXOMNI_URL ?? 'http://localhost',
    storageState: './auth-state.json',
    viewport: { width: 1440, height: 900 },
    screenshot: 'off',
    video: 'off',
    trace: 'off',
    actionTimeout: 15_000,
    navigationTimeout: 30_000,
  },
  projects: [
    {
      name: 'screenshots',
      use: { browserName: 'chromium' },
    },
  ],
});
