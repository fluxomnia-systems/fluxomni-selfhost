import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';

import type { APIRequestContext } from '@playwright/test';

import { requestGraphql } from './graphql';
import {
  cleanupSeededLibraryFiles,
  cleanupSeededRoutes,
  createRoute,
  uploadLibraryFile,
  type SeededRoute,
} from './seed';

export const V264_PREFIX = 'docs-v264';
export const V264_RUNDOWN_NAME = `Evening Program ${V264_PREFIX}`;

const SET_PLAYLIST = `
  mutation SetPlaylist(
    $routeId: RouteId!
    $expectedQueueRevision: String!
    $placements: [PlaylistPlacementInput!]!
  ) {
    playlist {
      setPlaylist(
        input: {
          routeId: $routeId
          expectedQueueRevision: $expectedQueueRevision
          placements: $placements
        }
      ) {
        status
        routeId
      }
    }
  }
`;

const ROUTE_PLAYLIST = `
  query RoutePlaylist($id: RouteId!) {
    routes {
      route(id: $id) {
        id
        playlist { queueRevision }
      }
    }
  }
`;

const LIST_RUNDOWNS = `
  query ListRundowns {
    rundowns {
      allRundowns { id name revision }
    }
  }
`;

const DELETE_RUNDOWN = `
  mutation DeleteRundown($input: DeleteRundownInput!) {
    rundowns {
      deleteRundown(input: $input) { status }
    }
  }
`;

const LIST_RECORDINGS = `
  query ListRecordings($after: String) {
    artifacts {
      libraryFiles(first: 50, after: $after, filter: { artifact: { kind: RECORDING } }) {
        nodes { id name contentType }
        hasNextPage
        endCursor
      }
    }
  }
`;

const LIST_NODES = `
  query ListFleetNodes {
    fleet {
      mediaNodes { id name }
    }
  }
`;

export type V264Scenario = {
  programRoute: SeededRoute;
  applyRoute: SeededRoute;
  videoNames: [string, string];
  videoIds: [string, string];
  photoNames: [string, string];
  photoIds: [string, string];
};

type ListedRundown = { id: string; name: string; revision: string };

export async function probeV264Api(api: APIRequestContext): Promise<void> {
  await requestGraphql(api, LIST_RUNDOWNS);
}

export async function cleanupV264(api: APIRequestContext): Promise<void> {
  await cleanupSeededRundowns(api, V264_PREFIX);
  await cleanupSeededRoutes(api, V264_PREFIX);
  await cleanupSeededLibraryFiles(api, V264_PREFIX);
}

export async function cleanupSeededRundowns(
  api: APIRequestContext,
  prefix: string,
): Promise<number> {
  let rundowns: ListedRundown[];
  try {
    const data = await requestGraphql<{ rundowns: { allRundowns: ListedRundown[] } }>(
      api,
      LIST_RUNDOWNS,
    );
    rundowns = data.rundowns.allRundowns;
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    if (/cannot query field .rundowns/i.test(message)) return 0;
    throw error;
  }

  const seeded = rundowns.filter((rundown) => rundown.name.includes(prefix));
  for (const rundown of seeded) {
    await requestGraphql(api, DELETE_RUNDOWN, {
      input: {
        id: rundown.id,
        expectedRevision: rundown.revision,
        requestId: crypto.randomUUID(),
      },
    });
  }
  return seeded.length;
}

export async function seedV264Scenario(api: APIRequestContext): Promise<V264Scenario> {
  const intro = `${V264_PREFIX}-intro-bumper.mp4`;
  const sponsor = `${V264_PREFIX}-sponsor-loop.mp4`;
  const blue = `${V264_PREFIX}-slide-blue.jpg`;
  const amber = `${V264_PREFIX}-slide-amber.jpg`;
  const video = createMediaFixture('mp4');
  const blueJpeg = createMediaFixture('jpg', '0x1d4ed8');
  const amberJpeg = createMediaFixture('jpg', '0xf59e0b');

  const videoIds: [string, string] = [
    await uploadLibraryFile(api, { name: intro, contentType: 'video/mp4', body: video }),
    await uploadLibraryFile(api, { name: sponsor, contentType: 'video/mp4', body: video }),
  ];
  const photoIds: [string, string] = [
    await uploadLibraryFile(api, { name: blue, contentType: 'image/jpeg', body: blueJpeg }),
    await uploadLibraryFile(api, { name: amber, contentType: 'image/jpeg', body: amberJpeg }),
  ];

  const programRoute = await createRoute(api, {
    key: `${V264_PREFIX}-playlist-program`,
    label: `Playlist Program ${V264_PREFIX}`,
  });
  const applyRoute = await createRoute(api, {
    key: `${V264_PREFIX}-apply-target`,
    label: `Apply Target ${V264_PREFIX}`,
  });
  await replacePlaylist(api, programRoute.id, videoIds);

  return {
    programRoute,
    applyRoute,
    videoNames: [intro, sponsor],
    videoIds,
    photoNames: [blue, amber],
    photoIds,
  };
}

export async function listRecordingNames(api: APIRequestContext): Promise<string[]> {
  const names: string[] = [];
  let after: string | null = null;
  for (;;) {
    const data: {
      artifacts: {
        libraryFiles: {
          nodes: Array<{ id: string; name: string }>;
          hasNextPage: boolean;
          endCursor: string | null;
        };
      };
    } = await requestGraphql(api, LIST_RECORDINGS, { after });
    const page = data.artifacts.libraryFiles;
    names.push(...page.nodes.map((node) => node.name));
    if (!page.hasNextPage || !page.endCursor || page.endCursor === after) return names;
    after = page.endCursor;
  }
}

export async function listFleetNodeIds(
  api: APIRequestContext,
): Promise<Array<{ id: string; name: string }>> {
  const data = await requestGraphql<{
    fleet: { mediaNodes: Array<{ id: string; name: string }> };
  }>(api, LIST_NODES);
  return data.fleet.mediaNodes;
}

async function replacePlaylist(
  api: APIRequestContext,
  routeId: string,
  fileIds: string[],
) {
  const revision = await readQueueRevision(api, routeId);
  await requestGraphql(api, SET_PLAYLIST, {
    routeId,
    expectedQueueRevision: revision,
    placements: fileIds.map((fileId) => ({ fileId })),
  });
}

async function readQueueRevision(api: APIRequestContext, routeId: string): Promise<string> {
  const deadline = Date.now() + 20_000;
  while (Date.now() < deadline) {
    const data = await requestGraphql<{
      routes: { route: { playlist: { queueRevision: string } } | null };
    }>(api, ROUTE_PLAYLIST, { id: routeId });
    const revision = data.routes.route?.playlist.queueRevision;
    if (revision) return revision;
    await new Promise((resolve) => setTimeout(resolve, 400));
  }
  throw new Error(`Route ${routeId} did not publish a playlist revision`);
}

function createMediaFixture(kind: 'mp4' | 'jpg', color = '0x1d4ed8'): Buffer {
  const dir = mkdtempSync(join(tmpdir(), 'fluxomni-v264-'));
  const output = join(dir, kind === 'mp4' ? 'fixture.mp4' : 'fixture.jpg');
  try {
    const args =
      kind === 'mp4'
        ? [
            '-y',
            '-hide_banner',
            '-loglevel',
            'error',
            '-f',
            'lavfi',
            '-i',
            'testsrc2=size=640x360:rate=30',
            '-f',
            'lavfi',
            '-i',
            'sine=frequency=440:sample_rate=48000',
            '-t',
            '4',
            '-c:v',
            'libx264',
            '-preset',
            'ultrafast',
            '-pix_fmt',
            'yuv420p',
            '-g',
            '30',
            '-c:a',
            'aac',
            '-b:a',
            '96k',
            '-movflags',
            '+faststart',
            output,
          ]
        : [
            '-y',
            '-hide_banner',
            '-loglevel',
            'error',
            '-f',
            'lavfi',
            '-i',
            `color=c=${color}:s=640x360`,
            '-frames:v',
            '1',
            output,
          ];
    const result = spawnSync('ffmpeg', args, { encoding: 'utf8' });
    if (result.status !== 0) {
      throw new Error(`ffmpeg fixture failed: ${result.stderr || result.stdout}`);
    }
    return readFileSync(output);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}
