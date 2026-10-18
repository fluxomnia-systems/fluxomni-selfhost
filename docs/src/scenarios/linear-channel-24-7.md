# Linear channel (24/7 broadcast)

## Who this is for

Broadcast operators running a 24/7 channel from pre-recorded content: corporate TV, radio stations with simulcast video, church service archives, esports replay channels. Use scheduled playback without an on-site encoder, with automatic recovery if a file fails to play.

## What you'll build

A single-host Fluxomni Studio install, or a small fleet for several regions. One route uses a large playlist from Google Drive, file-backup for fallback, and outputs to YouTube, a custom CDN, and Icecast audio.

```text
Files (local + Google Drive) → Playlist → Fluxomni Studio → { YouTube, Custom CDN, Icecast audio }
                                              ↘︎ file-backup loop (safety net)
```

## Setup

1. Install Fluxomni Studio: `curl -fsSL https://install.fluxomni.io | bash`.
2. Upload your files to Google Drive, organized by channel or day-part.
3. Add a Google Drive API key in **Settings → Artifacts → Google Drive**, then make the files link-shareable. See [Settings](../user-guide/settings.md#google-drive).
4. Create a route and add the playlist files in schedule order.
5. Attach a [file-backup source](../user-guide/routes.md) for fallback when a playlist file cannot play.
6. Configure outputs (RTMP/RTMPS, SRT, Icecast for the audio-only simulcast).
7. Start the route. Verify the HLS preview before going live.

## Cost and scale notes

Each channel uses decoding and playback resources plus outgoing bandwidth. The playlist has priority. File-backup loops play if a file fails. With [distributed mode](../user-guide/fleet.md), the route can recover from losing one node.

## Next steps

- [Fleet management](../user-guide/fleet.md)
- [Settings — artifact imports and media profiles](../user-guide/settings.md)
- [Backup and restore](../getting-started/backup.md)
