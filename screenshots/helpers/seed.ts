import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';

import type { APIRequestContext } from '@playwright/test';

import { requestGraphql } from './graphql';

// ---------------------------------------------------------------------------
// GraphQL operations
// ---------------------------------------------------------------------------

const SET_RESTREAM = `
  mutation SeedRoute(
    $label: Label
    $routeSources: RouteSourcesInput!
  ) {
    routes {
      setRoute(input: { label: $label, routeSources: $routeSources }) {
        routeId
      }
    }
  }
`;

const SET_OUTPUT = `
  mutation SeedOutput(
    $routeId: RouteId!
    $dst: OutputDstUrl!
    $label: Label
    $previewUrl: Url
    $mixins: [MixinSrcUrl!]!
  ) {
    routes {
      setOutput(
        input: {
          routeId: $routeId
          dst: $dst
          label: $label
          previewUrl: $previewUrl
          mixins: $mixins
        }
      ) {
        outputId
      }
    }
  }
`;

const REMOVE_RESTREAM = `
  mutation RemoveRoute($id: RouteId!) {
    routes {
      removeRoute(id: $id) {
        routeId
      }
    }
  }
`;

const DELETE_LIBRARY_FILES = `
  mutation DeleteLibraryFiles($ids: [FileId!]!) {
    artifacts { forceDeleteLibraryFiles(ids: $ids) { deleted failed { id message } } }
  }
`;

const LIST_RESTREAMS = `
  query ListRoutes {
    routes {
      allRoutes {
        id
        label
        outputs { id label }
      }
    }
  }
`;

const LIST_LIBRARY_FILES = `
  query ListLibraryFiles {
    artifacts {
      libraryFiles {
        id
        name
      }
    }
  }
`;

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type SeededRoute = {
  id: string;
  key: string;
  label: string;
};

type ListedRestream = {
  id: string;
  label: string | null;
  outputs: Array<{ id: string; label: string | null }> | null;
};

type ListedLibraryFile = {
  id: string;
  name: string;
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function rtmpPushRouteSources() {
  return {
    sources: [
      {
        role: 'PRIMARY_LIVE',
        order: 0,
        label: null,
        enabled: true,
        input: { rtmpPush: { reserved: false } },
      },
    ],
    failoverPolicy: {
      stickinessSecs: null,
      cooldownSecs: null,
    },
  };
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Creates a route via GraphQL and returns its id + key.
 */
export async function createRoute(
  api: APIRequestContext,
  opts: { key: string; label: string },
): Promise<SeededRoute> {
  const data = await requestGraphql<{ routes: { setRoute: { routeId: string } } }>(
    api,
    SET_RESTREAM,
    {
      label: opts.label,
      routeSources: rtmpPushRouteSources(),
    },
  );
  return { id: data.routes.setRoute.routeId, key: opts.key, label: opts.label };
}

/**
 * Adds an RTMP output destination to an existing route.
 */
export async function addOutput(
  api: APIRequestContext,
  opts: { restreamId: string; dst: string; label: string },
): Promise<string> {
  const data = await requestGraphql<{ routes: { setOutput: { outputId: string } } }>(
    api,
    SET_OUTPUT,
    {
      routeId: opts.restreamId,
      dst: opts.dst,
      label: opts.label,
      mixins: [],
    },
  );
  return data.routes.setOutput.outputId;
}

/**
 * Removes a single route by id.
 */
export async function removeRoute(
  api: APIRequestContext,
  restreamId: string,
): Promise<void> {
  await requestGraphql(api, REMOVE_RESTREAM, { id: restreamId });
}

/**
 * Lists all existing routes (for cleanup).
 */
export async function listRoutes(
  api: APIRequestContext,
): Promise<ListedRestream[]> {
  const data = await requestGraphql<{
    routes: { allRoutes: ListedRestream[] };
  }>(api, LIST_RESTREAMS);
  return data.routes.allRoutes;
}

/**
 * Removes all docs-created routes whose label includes the given prefix.
 * Returns the count of removed routes.
 */
export async function cleanupSeededRoutes(
  api: APIRequestContext,
  prefix: string,
): Promise<number> {
  const routes = await listRoutes(api);
  const seeded = routes.filter((r) => r.label?.includes(prefix));
  await Promise.all(seeded.map((r) => removeRoute(api, r.id)));
  return seeded.length;
}

/**
 * Removes all library files whose name starts with the given prefix.
 * Returns the count of removed files.
 */
export async function cleanupSeededLibraryFiles(
  api: APIRequestContext,
  prefix: string,
): Promise<number> {
  const data = await requestGraphql<{
    artifacts: { libraryFiles: ListedLibraryFile[] };
  }>(api, LIST_LIBRARY_FILES);
  const ids = data.artifacts.libraryFiles
    .filter((file) => file.name.startsWith(prefix))
    .map((file) => file.id);
  if (ids.length === 0) return 0;
  await requestGraphql(api, DELETE_LIBRARY_FILES, { ids });
  return ids.length;
}

function createValid720p30Fixture(): Buffer {
  const dir = mkdtempSync(join(tmpdir(), 'fluxomni-docs-artifact-'));
  const output = join(dir, 'fixture-720p30.mp4');
  try {
    const result = spawnSync(
      'ffmpeg',
      [
        '-y',
        '-hide_banner',
        '-loglevel',
        'error',
        '-f',
        'lavfi',
        '-i',
        'testsrc2=size=1280x720:rate=30',
        '-f',
        'lavfi',
        '-i',
        'sine=frequency=660:sample_rate=48000',
        '-t',
        '6',
        '-c:v',
        'libx264',
        '-preset',
        'ultrafast',
        '-pix_fmt',
        'yuv420p',
        '-g',
        '60',
        '-c:a',
        'aac',
        '-b:a',
        '128k',
        '-movflags',
        '+faststart',
        output,
      ],
      { encoding: 'utf8' },
    );
    if (result.status !== 0) {
      throw new Error(
        `ffmpeg fixture generation failed: ${result.stderr || result.stdout}`,
      );
    }
    return readFileSync(output);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

/**
 * Uploads small valid 720p30 H.264/AAC MP4 artifacts through the same `/files`
 * surface the Control Surface uses.
 */
export async function seedArtifactLibraryScenario(
  api: APIRequestContext,
  prefix: string,
): Promise<void> {
  const fixture = createValid720p30Fixture();
  const names = [
    `${prefix}-intro-bumper.mp4`,
    `${prefix}-sponsor-loop.mp4`,
    `${prefix}-fallback-slate.mp4`,
  ];
  for (const name of names) {
    const response = await api.post('/files', {
      headers: {
        'content-type': 'video/mp4',
        'x-file-name': encodeURIComponent(name),
      },
      data: fixture,
    });
    if (!response.ok()) {
      throw new Error(`Artifact seed upload failed (${response.status()})`);
    }
  }
}

// ---------------------------------------------------------------------------
// Scenario builders
// ---------------------------------------------------------------------------

/**
 * Seeds the "realistic routes list" scenario used for page-level screenshots.
 * Creates multiple routes with outputs to give the UI a populated look.
 */
export async function seedRoutesListScenario(
  api: APIRequestContext,
  prefix: string,
): Promise<SeededRoute[]> {
  const routes: SeededRoute[] = [];

  const main = await createRoute(api, {
    key: `${prefix}-main-broadcast`,
    label: `Main Broadcast ${prefix}`,
  });
  await addOutput(api, {
    restreamId: main.id,
    dst: 'rtmp://a.rtmp.youtube.com/live2/stream-key',
    label: 'YouTube Live',
  });
  await addOutput(api, {
    restreamId: main.id,
    dst: 'rtmp://live.twitch.tv/app/stream-key',
    label: 'Twitch',
  });
  routes.push(main);

  const backup = await createRoute(api, {
    key: `${prefix}-backup-feed`,
    label: `Backup Feed ${prefix}`,
  });
  await addOutput(api, {
    restreamId: backup.id,
    dst: 'rtmp://backup.cdn.example.com/live/backup',
    label: 'CDN Backup',
  });
  routes.push(backup);

  const event = await createRoute(api, {
    key: `${prefix}-event-stream`,
    label: `Event Stream ${prefix}`,
  });
  await addOutput(api, {
    restreamId: event.id,
    dst: 'rtmp://live-api-s.facebook.com:443/rtmp/stream-key',
    label: 'Facebook Live',
  });
  await addOutput(api, {
    restreamId: event.id,
    dst: 'rtmp://a.rtmp.youtube.com/live2/event-key',
    label: 'YouTube Events',
  });
  await addOutput(api, {
    restreamId: event.id,
    dst: 'rtmp://live.twitch.tv/app/event-key',
    label: 'Twitch Events',
  });
  routes.push(event);

  return routes;
}
