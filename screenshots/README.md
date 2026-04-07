# Selfhost Docs Screenshots

Playwright-based screenshot automation for the FluxOmni selfhost user-guide
documentation. Connects to a running FluxOmni instance, seeds realistic data
via GraphQL, and captures page-level plus guided-flow screenshots.

## Quick Start

```bash
cd screenshots
npm install
npx playwright install chromium

# Capture against a local instance (default http://localhost)
npm run capture

# Capture against a specific instance
FLUXOMNI_URL=http://192.168.1.100 npm run capture

# Run headed to watch the browser
npm run capture:headed
```

## Environment Variables

| Variable                  | Default             | Description                       |
|---------------------------|---------------------|-----------------------------------|
| `FLUXOMNI_URL`            | `http://localhost`  | Base URL of the FluxOmni instance |
| `FLUXOMNI_ADMIN_USER`     | `admin`             | Admin username for login          |
| `FLUXOMNI_ADMIN_PASSWORD` | _(empty)_           | Admin password (required if auth is on) |

## Output

Screenshots are written directly to `docs/src/images/user-guide/`:

**Page screenshots** (replace one-to-one the images referenced in the mdBook):
- `routes-list.jpg`
- `create-route.jpg`
- `route-workspace.jpg`
- `attention.jpg`
- `fleet.jpg`
- `settings.jpg`

**Guided-flow screenshots** (step-by-step captures in `flows/`):
- `flows/create-route-1-open.jpg` … `flows/create-route-4-created.jpg`
- `flows/add-output-1-workspace.jpg` … `flows/add-output-3-added.jpg`

## From the repo root

```bash
make screenshots
```
