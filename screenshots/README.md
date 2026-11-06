# Selfhost Docs Screenshots

Playwright-based screenshot automation for the Fluxomni selfhost user guide. The capture suite connects to a running Fluxomni instance, signs in as an admin when required, seeds realistic route data through GraphQL, and writes the resulting screenshots directly into the mdBook image tree.

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

# Capture only the short landing/product overview video
FLUXOMNI_URL=http://192.168.1.100 FLUXOMNI_ADMIN_PASSWORD=secret npm run capture:overview

# Capture v26.4.0 operator surfaces (rundowns, playlist, library, fleet)
FLUXOMNI_URL=http://192.168.1.100 FLUXOMNI_ADMIN_PASSWORD=secret npm run capture:v264

# Run headed to watch the browser
npm run capture:headed
npm run capture:v264:headed
```

## Environment Variables

| Variable | Default | Description |
| --- | --- | --- |
| `FLUXOMNI_URL` | `http://localhost` | Base URL of the Fluxomni instance |
| `FLUXOMNI_ADMIN_USER` | `admin` | Admin username for login |
| `FLUXOMNI_ADMIN_PASSWORD` | _(empty)_ | Admin password, required when auth is enabled |
| `FLUXOMNI_VIDEO_OUTPUT_DIR` | suite default | Optional directory for guided and v26.4.0 WebMs |

Regenerating images and videos requires a reachable Fluxomni instance. v26.4.0 stills and WebMs require a **v26.4.0** instance. Passwords, enrollment codes, stream keys, and Tailscale-only hosts stay in the environment or on the live page; they are not written into this repository. When `FLUXOMNI_URL` is unset, the suite tries `http://localhost`. If that instance is down or returns an error, the capture run skips instead of failing, so docs CI does not need a live stack.

## What the suite captures

### Page screenshots

These replace the top-level images referenced from the user-guide pages in `docs/src/images/user-guide/`:

- `routes-list.jpg`
- `create-route.jpg`
- `route-workspace.jpg`
- `route-routing.jpg`
- `route-edit-advanced.jpg`
- `artifacts.jpg`
- `artifacts-add-files.jpg`
- `artifacts-storage.jpg`
- `attention.jpg`
- `fleet.jpg`
- `settings.jpg`
- `settings-artifacts.jpg`
- `settings-media-profiles.jpg`
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

The guided-flow suite also records short interaction videos in `screenshots/recordings/user-guide/` by default.
Set `FLUXOMNI_VIDEO_OUTPUT_DIR` to place the recordings somewhere else:

- `create-route.webm`
- `add-output.webm`
- `flow-overview.webm`

The videos start from the loaded Routes page, then use mouse movement, short pauses, and delayed typing for readable pacing. Each flow asserts the important intermediate UI state is visible, then returns to the Routes page before ending.

`flow-overview.webm` is the landing-oriented overview. It creates an RTMP route through the UI, reads the generated publish URL, starts an FFmpeg publisher, waits for the route to become live, opens the HLS preview, adds a YouTube-style output, and saves the recorded browser interaction.

### v26.4.0 operator surfaces

`npm run capture:v264` drives the Fluxomni web app surfaces added in v26.4.0. It seeds only routes, library files, and rundowns whose names include `docs-v264`, then deletes those objects. It does not change Fleet admission limits, start playlist playback, submit preparation or slideshow render jobs, or issue an enrollment code.

Stills are written to `docs/src/images/user-guide/v264/` when the UI can be driven:

- `rundowns.jpg` — Rundowns editor with planned total and library order
- `rundown-duplicate.jpg` — duplicated saved revision
- `rundown-apply.jpg` — apply that revision to a suite-owned idle route with no schedule
- `playlist-timing.jpg` — planned item timing and program total
- `playlist-stinger.jpg` — stinger clip selected from the library
- `playlist-schedule.jpg` — weekday schedule, IANA zone, and next occurrence
- `playlist-cue.jpg` — timestamp editor when cueing is enabled, otherwise the idle progress line
- `playlist-prepare.jpg` — unchecked "Prepare selected videos" option in the playlist picker; the suite does not choose it or run **Normalize files**
- `route-readiness.jpg` — readiness checklist for the playlist flow
- `artifacts-slideshow.jpg` — photo order and five-second timing, before render
- `artifacts-thumbnails.jpg` — thumbnail state for an uploaded video
- `artifacts-recording.jpg` — recording preview and preserve state, only when a recording already exists
- `fleet-control.jpg` — control connection shown separately from media access
- `fleet-capacity.jpg` — route and output ceilings and reserved demand
- `fleet-preparation.jpg` — preparation CPU, memory, task, and queue figures
- `fleet-enroll.jpg` — Add Node enrollment form, with secrets masked

Short WebMs use the same callout pacing as the guided flows. They land in `screenshots/recordings/user-guide/` unless `FLUXOMNI_VIDEO_OUTPUT_DIR` is set:

- `rundowns.webm` — create, save, and duplicate a rundown
- `playlist-programming.webm` — timing, stinger, weekday schedule, and readiness

#### Not captured automatically

These stay out of the suite because the UI action is unsafe, depends on lab state the suite must not invent, or the control stays disabled until real playback:

- Timestamp cue and scrub while media is playing. The editor is captured only when **Edit playback time** is already enabled. The suite does not start playout to force it.
- Slideshow render. Composition stops before **Create video**, which publishes an MP4 to object storage.
- Recording preserve, FLV preview, and retention. Those shots run only when a `RECORDING` file is already in the Library. The suite does not create one.
- Enrollment issuance. The Add Node form is opened and **Generate join command** is not clicked. Commands, one-time codes, private keys, and Tailscale hosts are masked before the still.
- Capacity ceiling edits. The form is shown and **Save limits** is not clicked.
- Preparation jobs. The prepare control and Fleet preparation panel are shown. No preparation job is submitted.
- Apply rundown against an existing lab route. Apply runs only on the idle `docs-v264` route created for the capture, and only when that route has no schedule.

## From the repo root

```bash
make screenshots
```

Use the root-level wrapper when you want the same install and capture behavior that the main README documents.
