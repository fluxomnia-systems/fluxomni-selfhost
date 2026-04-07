import type { APIRequestContext } from '@playwright/test';

import { requestGraphql } from './graphql';

// ---------------------------------------------------------------------------
// GraphQL operations
// ---------------------------------------------------------------------------

const SET_RESTREAM = `
  mutation SeedRoute(
    $key: RestreamKey!
    $label: Label
    $ingressGroup: IngressGroupInput!
  ) {
    stream {
      setRestream(key: $key, label: $label, ingressGroup: $ingressGroup)
    }
  }
`;

const SET_OUTPUT = `
  mutation SeedOutput(
    $restreamId: RestreamId!
    $dst: OutputDstUrl!
    $label: Label
    $previewUrl: Url
    $mixins: [MixinSrcUrl!]!
  ) {
    stream {
      setOutput(
        restreamId: $restreamId
        dst: $dst
        label: $label
        previewUrl: $previewUrl
        mixins: $mixins
      )
    }
  }
`;

const REMOVE_RESTREAM = `
  mutation RemoveRoute($id: RestreamId!) {
    stream { removeRestream(id: $id) }
  }
`;

const LIST_RESTREAMS = `
  query ListRoutes {
    stream {
      allRestreams {
        id
        key
        label
        outputs { id label }
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
  key: string;
  label: string | null;
  outputs: Array<{ id: string; label: string | null }> | null;
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function rtmpPushIngressGroup(keys: string[]) {
  return {
    policy: null,
    manualOverrideId: null,
    ingresses: keys.map((key) => ({
      key,
      label: null,
      enabled: true,
      protocol: { rtmpPush: { reserved: false } },
    })),
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
  const data = await requestGraphql<{ stream: { setRestream: string } }>(
    api,
    SET_RESTREAM,
    {
      key: opts.key,
      label: opts.label,
      ingressGroup: rtmpPushIngressGroup(['primary']),
    },
  );
  return { id: data.stream.setRestream, key: opts.key, label: opts.label };
}

/**
 * Adds an RTMP output destination to an existing route.
 */
export async function addOutput(
  api: APIRequestContext,
  opts: { restreamId: string; dst: string; label: string },
): Promise<string> {
  const data = await requestGraphql<{ stream: { setOutput: string } }>(
    api,
    SET_OUTPUT,
    {
      restreamId: opts.restreamId,
      dst: opts.dst,
      label: opts.label,
      mixins: [],
    },
  );
  return data.stream.setOutput;
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
    stream: { allRestreams: ListedRestream[] };
  }>(api, LIST_RESTREAMS);
  return data.stream.allRestreams;
}

/**
 * Removes all routes whose key starts with the given prefix.
 * Returns the count of removed routes.
 */
export async function cleanupSeededRoutes(
  api: APIRequestContext,
  prefix: string,
): Promise<number> {
  const routes = await listRoutes(api);
  const seeded = routes.filter((r) => r.key.startsWith(prefix));
  await Promise.all(seeded.map((r) => removeRoute(api, r.id)));
  return seeded.length;
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
    label: 'Main Broadcast',
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
    label: 'Backup Feed',
  });
  await addOutput(api, {
    restreamId: backup.id,
    dst: 'rtmp://backup.cdn.example.com/live/backup',
    label: 'CDN Backup',
  });
  routes.push(backup);

  const event = await createRoute(api, {
    key: `${prefix}-event-stream`,
    label: 'Event Stream',
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
