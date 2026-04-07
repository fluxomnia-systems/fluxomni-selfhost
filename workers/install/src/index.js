const SCRIPT_BASE = "https://raw.githubusercontent.com/fluxomnia-systems/fluxomni-selfhost";

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const path = url.pathname;

    // install.fluxomni.io/ or install.fluxomni.io/install.sh
    // → latest stable from main
    if (path === "/" || path === "/install.sh") {
      const ref = url.searchParams.get("ref") || "main";
      return proxyScript(ref);
    }

    // install.fluxomni.io/v1.2.3 → pinned version
    const versionMatch = path.match(/^\/(v[\d.]+)$/);
    if (versionMatch) {
      return proxyScript(versionMatch[1], true);
    }

    return new Response(
      [
        "FluxOmni Installer",
        "",
        "Usage:",
        "  curl -fsSL https://install.fluxomni.io | bash",
        "",
        "Pinned version:",
        "  curl -fsSL https://install.fluxomni.io/v1.2.3 | bash",
        "",
        "Edge channel:",
        '  curl -fsSL "https://install.fluxomni.io?ref=edge" | bash',
        "",
      ].join("\n"),
      {
        status: 404,
        headers: { "Content-Type": "text/plain; charset=utf-8" },
      }
    );
  },
};

async function proxyScript(ref, fallbackToMain = false) {
  const upstream = `${SCRIPT_BASE}/${ref}/install.sh`;
  const resp = await fetch(upstream, {
    headers: { "User-Agent": "FluxOmni-Install-Proxy/1.0" },
  });

  if (!resp.ok && fallbackToMain) {
    const fallback = await fetch(`${SCRIPT_BASE}/main/install.sh`, {
      headers: { "User-Agent": "FluxOmni-Install-Proxy/1.0" },
    });
    if (!fallback.ok) {
      return new Response(`Failed to fetch install script (ref=${ref}, fallback=main)\n`, {
        status: 502,
        headers: { "Content-Type": "text/plain" },
      });
    }
    return new Response(fallback.body, {
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
        "Cache-Control": "public, max-age=300",
        "X-FluxOmni-Ref": "main",
        "X-FluxOmni-Requested-Ref": ref,
      },
    });
  }

  if (!resp.ok) {
    return new Response(`Failed to fetch install script (ref=${ref})\n`, {
      status: 502,
      headers: { "Content-Type": "text/plain" },
    });
  }

  return new Response(resp.body, {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": ref === "main" ? "public, max-age=300" : "public, max-age=3600",
      "X-FluxOmni-Ref": ref,
    },
  });
}
