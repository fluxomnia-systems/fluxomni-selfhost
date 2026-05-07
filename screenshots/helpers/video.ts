import { mkdirSync, renameSync, rmSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { dirname } from 'node:path';

import { type Browser, type Page } from '@playwright/test';

type BrowserContext = Awaited<ReturnType<Browser['newContext']>>;

const DEFAULT_TRIM_SECONDS = Number(
  process.env.FLUXOMNI_VIDEO_TRIM_START_SECONDS ?? '5.5',
);

export async function saveRecordedVideo(
  page: Page,
  context: BrowserContext,
  outputPath: string,
  options: { trimStartSeconds?: number } = {},
) {
  mkdirSync(dirname(outputPath), { recursive: true });
  const video = page.video();
  await context.close();
  if (!video) return;

  const rawPath = `${outputPath}.raw.webm`;
  rmSync(rawPath, { force: true });
  await video.saveAs(rawPath);

  const trimStartSeconds = options.trimStartSeconds ?? DEFAULT_TRIM_SECONDS;
  if (trimStartSeconds <= 0) {
    renameSync(rawPath, outputPath);
    return;
  }

  trimVideoLeadIn(rawPath, outputPath, trimStartSeconds);
  rmSync(rawPath, { force: true });
}

function trimVideoLeadIn(inputPath: string, outputPath: string, seconds: number) {
  const result = spawnSync(
    'ffmpeg',
    [
      '-y',
      '-hide_banner',
      '-loglevel',
      'error',
      '-i',
      inputPath,
      '-ss',
      String(seconds),
      '-c:v',
      'libvpx',
      '-crf',
      '10',
      '-b:v',
      '1M',
      '-deadline',
      'good',
      '-cpu-used',
      '4',
      '-c:a',
      'libopus',
      outputPath,
    ],
    { encoding: 'utf8' },
  );

  if (result.status !== 0) {
    throw new Error(
      `ffmpeg could not trim video lead-in: ${result.stderr || result.stdout}`,
    );
  }
}
