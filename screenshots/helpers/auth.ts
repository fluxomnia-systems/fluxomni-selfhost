import { request, type APIRequestContext } from '@playwright/test';

type SessionStatus = {
  authRequired: boolean;
  authenticated: boolean;
};

/**
 * Creates an authenticated Playwright API request context.
 *
 * When the instance has auth enabled it logs in with the provided credentials.
 * When auth is disabled it returns an unauthenticated context directly.
 */
export async function createAuthenticatedApi(
  baseURL: string,
): Promise<APIRequestContext> {
  const username = process.env.FLUXOMNI_ADMIN_USER ?? 'admin';
  const password = process.env.FLUXOMNI_ADMIN_PASSWORD ?? '';

  const api = await request.newContext({
    baseURL,
    extraHTTPHeaders: { 'content-type': 'application/json' },
  });

  const statusResponse = await api.get('/api/auth/status');
  if (!statusResponse.ok()) {
    throw new Error(
      `Cannot reach FluxOmni at ${baseURL} (status ${statusResponse.status()})`,
    );
  }

  const status = (await statusResponse.json()) as SessionStatus;

  if (!status.authRequired) {
    return api;
  }

  if (!password) {
    await api.dispose();
    throw new Error(
      'FluxOmni auth is enabled — set FLUXOMNI_ADMIN_PASSWORD before capturing screenshots',
    );
  }

  const loginResponse = await api.post('/api/auth/login', {
    data: { username, password },
  });

  if (!loginResponse.ok()) {
    const body = await loginResponse.text();
    await api.dispose();
    throw new Error(
      `Login failed for "${username}" (${loginResponse.status()}): ${body}`,
    );
  }

  return api;
}
