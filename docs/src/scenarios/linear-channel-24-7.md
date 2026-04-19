# Linear channel (24/7 broadcast)

## Who this is for

Broadcast operators running a 24/7 channel from pre-recorded content: corporate TV, radio stations with simulcast video, church service archives, esports replay channels. You want scheduled playback without an on-site encoder, and automatic recovery if a file fails to play.

## What you'll build

FluxOmni single-host (or a small fleet if you need regional reach), one route with a large playlist backed by Google Drive, file-backup as the safety net, and outputs to YouTube + custom CDN + Icecast audio.

```text
Files (local + Google Drive) → Playlist → FluxOmni → { YouTube, Custom CDN, Icecast audio }
                                              ↘︎ file-backup loop (safety net)
```

## Setup

1. Install FluxOmni: `curl -fsSL https://install.fluxomni.io | bash`.
2. Upload your files to Google Drive, organized by channel or day-part.
3. Link the Drive account in Settings. See [Configuration](../getting-started/configuration.md).
4. Create a route and add the playlist files in schedule order.
5. Attach a [file-backup source](../user-guide/routes.md) as a safety net for the route.
6. Configure outputs (RTMP/RTMPS, SRT, Icecast for the audio-only simulcast).
7. Start the route. Verify the HLS preview before going live.

## Cost and scale notes

Per-channel cost is the decoder/playback cost plus egress bandwidth. The playlist takes precedence; file-backup loops underneath if a file fails. Once [distributed mode](../user-guide/fleet.md) is enabled, the route survives single-node loss.

## Next steps

- [Fleet management](../user-guide/fleet.md)
- [Settings — audio mixing and Google Drive](../user-guide/settings.md)
- [Backup and restore](../getting-started/backup.md)
