# Artifact library for playout assets

## Who this is for

Operators who reuse the same source files across playlists, fallback loops, client channels, or regional media nodes. Use one persistent artifact catalog so you can find files without searching each route or node.

## What you'll build

A shared artifact library with browser uploads, folder uploads, Google Drive imports, tags, storage limits, and file selection for route playlists from the same catalog.

```text
Local files / folders / Google Drive → Artifacts → playlists and file-backup sources
                                           ↘ storage usage and cache visibility
```

## Setup

1. Install Fluxomni Studio: `curl -fsSL https://install.fluxomni.io | bash`.
2. Open **Artifacts** from the Control Surface sidebar.
3. Use **Add files** to upload a file, upload a folder, or import from Google Drive.
4. Tag reusable files by campaign, client, show, or day-part.
5. Check the storage chip and expandable storage panel before large uploads.
6. Open a route playlist and choose files from **From library** instead of importing the same file again.
7. Use Fleet to confirm which media nodes have cached the required artifacts.

## Cost and scale notes

Artifacts are stored in the control-plane relay backend by default. New files are accepted only within the configured storage headroom. Media nodes cache artifacts when a route manifest needs them. Regional nodes do not need permanent copies of the full catalog.

## Next steps

- [Artifacts user guide](../user-guide/artifacts.md)
- [Routes and playlists](../user-guide/routes.md#playlist)
- [Fleet management](../user-guide/fleet.md)
