# Selfhost Docs Screenshots

Playwright-based screenshot automation for the FluxOmni selfhost user guide. The capture suite connects to a running FluxOmni instance, signs in as an admin when required, seeds realistic route data through GraphQL, and writes the resulting screenshots directly into the mdBook image tree.

## Quick Start

```bash
cd screenshots
npm install
npx playwright install chromium

# Capture against a local instance (default http://localhost)
npm run capture

# Capture against a specific instance
FLUXOMNI_URL=http://192.168.1.100 npm run capture

# Capture against an auth-enabled instance
FLUXOMNI_URL=http://192.168.1.100 FLUXOMNI_ADMIN_PASSWORD=secret npm run capture

# Run headed to watch the browser
npm run capture:headed
```

## Environment Variables

| Variable | Default | Description |
| --- | --- | --- |
| `FLUXOMNI_URL` | `http://localhost` | Base URL of the FluxOmni instance |
| `FLUXOMNI_ADMIN_USER` | `admin` | Admin username for login |
| `FLUXOMNI_ADMIN_PASSWORD` | _(empty)_ | Admin password, required when auth is enabled |

## What the suite captures

### Page screenshots

These replace the top-level images referenced from the user-guide pages in `docs/src/images/user-guide/`:

- `routes-list.jpg`
- `create-route.jpg`
- `route-workspace.jpg`
- `route-routing.jpg`
- `route-edit-advanced.jpg`
- `attention.jpg`
- `fleet.jpg`
- `settings.jpg`
- `settings-security.jpg`
- `settings-users.jpg`
- `login.jpg`

### Guided flows

These step-by-step walkthrough images are written to `docs/src/images/user-guide/flows/`:

- `create-route-1-open.jpg`
- `create-route-2-dialog.jpg`
- `create-route-3-identity.jpg`
- `create-route-4-created.jpg`
- `add-output-1-workspace.jpg`
- `add-output-2-dialog.jpg`
- `add-output-3-added.jpg`

## From the repo root

```bash
make screenshots
```

Use the root-level wrapper when you want the same install and capture behavior that the main README documents.
