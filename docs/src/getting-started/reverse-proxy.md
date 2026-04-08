# Reverse Proxy & TLS

Most production deployments place FluxOmni behind a reverse proxy to
terminate TLS, serve the UI on port 443, and optionally restrict access.

## Overview

FluxOmni exposes an HTTP surface (UI + API) and several media-plane ports.
A reverse proxy sits in front of the HTTP surface while media ports
(RTMP, SRT, HLS/WebRTC) are typically passed through directly.

```text
Internet
  |
  +---> :443 (TLS) ---> reverse proxy ---> control-plane :80  (HTTP)
  +---> :1935 -----------------------------------------> media-node   (RTMP)
  +---> :10080/udp ------------------------------------> media-node   (SRT)
  +---> :8000 -----------------------------------------> media-node   (HLS/WebRTC)
```

## Caddy (recommended)

Caddy handles TLS certificates automatically via Let's Encrypt.

Install Caddy on the same host or a gateway host, then create
`/etc/caddy/Caddyfile`:

```text
stream.example.com {
    reverse_proxy localhost:80
}
```

Reload Caddy:

```bash
sudo systemctl reload caddy
```

Caddy provisions a certificate automatically. Set your `.env` values to
match:

```bash
FLUXOMNI_PUBLIC_HOST=stream.example.com
FLUXOMNI_MEDIA_NODE_PUBLIC_HOST=stream.example.com
```

Then restart the stack:

```bash
docker compose up -d
```

### WebSocket support

The Control Surface uses WebSocket connections for real-time updates. Caddy
proxies WebSocket by default with no extra configuration.

## nginx

Install nginx and create `/etc/nginx/sites-available/fluxomni`:

```nginx
server {
    listen 443 ssl http2;
    server_name stream.example.com;

    ssl_certificate     /etc/letsencrypt/live/stream.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/stream.example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

server {
    listen 80;
    server_name stream.example.com;
    return 301 https://$host$request_uri;
}
```

Enable the site and reload:

```bash
sudo ln -s /etc/nginx/sites-available/fluxomni /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

Obtain a certificate with Certbot:

```bash
sudo certbot --nginx -d stream.example.com
```

## Media ports

RTMP (TCP 1935), SRT (UDP 10080), and HLS/WebRTC (TCP+UDP 8000) carry
media traffic that is not typically proxied through an HTTP reverse proxy.
Leave these ports published directly on the host.

If you need TLS on RTMP, some CDN endpoints accept RTMPS. FluxOmni
outputs support `rtmps://` destination URLs natively.

## Firewall considerations

When using a reverse proxy, you can restrict the control-plane HTTP port
to localhost so it is only reachable through the proxy:

```bash
# In .env
FLUXOMNI_CONTROL_PLANE_HTTP_PORT=127.0.0.1:80
```

This binds port 80 to the loopback interface only. The reverse proxy
on the same host can still reach it, but external clients cannot bypass
TLS.

Media ports must remain publicly accessible for publishers and viewers.
