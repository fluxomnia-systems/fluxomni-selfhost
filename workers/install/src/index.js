const SCRIPT_BASE = "https://raw.githubusercontent.com/fluxomnia-systems/fluxomni-selfhost";

export default {
  async fetch(request) {
    const url = new URL(request.url);
    if (url.pathname === "/" || url.pathname === "/install.sh") {
      return proxyScript(url.searchParams.get("ref") || "main");
    }

    const version = url.pathname.match(/^\/(v[\d.]+)$/)?.[1];
    if (version) {
      // Always use the release-aware launcher, including for historical tags.
      return proxyScript("main", version);
    }

    return new Response([
      "Fluxomni Studio Installer", "",
      "Usage: curl -fsSL https://install.fluxomni.io | bash", "",
      "Pinned version: curl -fsSL https://install.fluxomni.io/v26.3.2 | bash", "",
      "Edge: curl -fsSL https://install.fluxomni.io | FLUXOMNI_VERSION=edge bash", "",
    ].join("\n"), { status: 404, headers: { "Content-Type": "text/plain; charset=utf-8" } });
  },
};

async function proxyScript(ref, version) {
  const upstream = await fetch(`${SCRIPT_BASE}/${ref}/install.sh`, {
    headers: { "User-Agent": "Fluxomni-Install-Proxy/1.0" },
  });
  if (!upstream.ok || !upstream.body) {
    return new Response(`Failed to fetch install launcher (ref=${ref})\n`, {
      status: 502, headers: { "Content-Type": "text/plain; charset=utf-8" },
    });
  }

  const headers = {
    "Content-Type": "text/plain; charset=utf-8",
    "Cache-Control": ref === "main" ? "public, max-age=300" : "public, max-age=3600",
    "X-Fluxomni-Ref": ref,
  };
  if (!version) return new Response(upstream.body, { headers });
  headers["X-Fluxomni-Requested-Ref"] = version;
  const reader = upstream.body.getReader();
  let prefixSent = false;
  const body = new ReadableStream({
    async pull(controller) {
      if (!prefixSent) {
        controller.enqueue(new TextEncoder().encode(`#!/usr/bin/env bash\nexport FLUXOMNI_VERSION='${version}'\n`));
        prefixSent = true;
        return;
      }
      const { done, value } = await reader.read();
      if (done) controller.close(); else controller.enqueue(value);
    },
    cancel(reason) { return reader.cancel(reason); },
  });
  return new Response(body, { headers });
}
