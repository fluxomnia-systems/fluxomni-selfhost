import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import { test } from 'node:test';

const source = await readFile(new URL('../src/index.js', import.meta.url), 'utf8');
const worker = (await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`)).default;
const base = 'https://raw.githubusercontent.com/fluxomnia-systems/fluxomni-selfhost';

async function responseFor(path, callback, script = 'printf "%s" "$FLUXOMNI_VERSION"', status = 200) {
  const original = globalThis.fetch;
  const requests = [];
  globalThis.fetch = async (url) => {
    requests.push(url);
    return new Response(script, { status });
  };
  try {
    await callback(await worker.fetch(new Request(`https://install.fluxomni.io${path}`)), requests);
  } finally {
    globalThis.fetch = original;
  }
}

// @lat: [[installation#Public proxy pin tests]]
test('historical and future URL pins use the release-aware launcher and override latest', async () => {
  for (const version of ['v26.3.2', 'v26.4.0']) {
    await responseFor(`/${version}`, async (response, requests) => {
      assert.equal(response.status, 200);
      assert.deepEqual(requests, [`${base}/main/install.sh`]);
      assert.equal(response.headers.get('X-Fluxomni-Requested-Ref'), version);
      const script = await response.text();
      const executed = spawnSync('bash', ['-s'], {
        input: script, encoding: 'utf8', env: { ...process.env, FLUXOMNI_VERSION: 'latest' },
      });
      assert.equal(executed.status, 0, executed.stderr);
      assert.equal(executed.stdout, version);
    });
  }
});

test('default and custom script refs stream the original script without changing its channel', async () => {
  for (const [path, ref] of [['/', 'main'], ['/install.sh', 'main'], ['/?ref=candidate', 'candidate']]) {
    await responseFor(path, async (response, requests) => {
      assert.equal(response.status, 200);
      assert.deepEqual(requests, [`${base}/${ref}/install.sh`]);
      assert.equal(await response.text(), 'printf "%s" "$FLUXOMNI_VERSION"');
    });
  }
});

test('versioned routes fail when the launcher is unavailable rather than running another release', async () => {
  await responseFor('/v26.3.2', async (response, requests) => {
    assert.equal(response.status, 502);
    assert.deepEqual(requests, [`${base}/main/install.sh`]);
  }, 'not found', 404);
});

test('unsupported paths return help without fetching a script', async () => {
  await responseFor('/not-a-release', async (response, requests) => {
    assert.equal(response.status, 404);
    assert.deepEqual(requests, []);
  });
});
