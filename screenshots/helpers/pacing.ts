import { expect, type Locator, type Page } from '@playwright/test';

type CalloutSide = 'left' | 'right' | 'top' | 'bottom';

export async function clearCallouts(page: Page) {
  await page.evaluate(() => {
    document.querySelectorAll('.docs-callout-layer').forEach((node) => {
      node.remove();
    });
  });
}

export async function addCallout(
  page: Page,
  target: Locator,
  label: string,
  side: CalloutSide = 'left',
) {
  await clearCallouts(page);
  const box = await target.first().boundingBox();
  if (!box) return;

  await page.evaluate(
    ({ box, label, side }) => {
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;
      const targetX = box.x + box.width / 2;
      const targetY = box.y + box.height / 2;
      const bubbleWidth = 220;
      const bubbleHeight = 54;
      const margin = 24;
      let bubbleX = targetX - bubbleWidth / 2;
      let bubbleY = targetY - bubbleHeight / 2;

      if (side === 'left') {
        bubbleX =
          box.x - bubbleWidth - 28 >= margin
            ? box.x - bubbleWidth - 28
            : box.x + box.width + 28;
      } else if (side === 'right') {
        bubbleX =
          box.x + box.width + 28 + bubbleWidth <= viewportWidth - margin
            ? box.x + box.width + 28
            : box.x - bubbleWidth - 28;
      } else if (side === 'top') {
        bubbleY = box.y - bubbleHeight - 28;
      } else {
        bubbleY = box.y + box.height + 28;
      }

      bubbleX = Math.max(margin, Math.min(viewportWidth - bubbleWidth - margin, bubbleX));
      bubbleY = Math.max(
        margin,
        Math.min(viewportHeight - bubbleHeight - margin, bubbleY),
      );

      const startX =
        bubbleX +
        (bubbleX < box.x ? bubbleWidth : bubbleX > box.x + box.width ? 0 : bubbleWidth / 2);
      const startY =
        bubbleY +
        (side === 'top' ? bubbleHeight : side === 'bottom' ? 0 : bubbleHeight / 2);

      const layer = document.createElement('div');
      layer.className = 'docs-callout-layer';
      layer.style.position = 'fixed';
      layer.style.inset = '0';
      layer.style.zIndex = '2147483647';
      layer.style.pointerEvents = 'none';
      layer.style.fontFamily =
        'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';

      layer.innerHTML = `
        <svg width="100%" height="100%" style="position:absolute;inset:0;overflow:visible">
          <defs>
            <marker id="docs-callout-arrow" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto">
              <path d="M 0 0 L 12 6 L 0 12 z" fill="#dc2626"></path>
            </marker>
          </defs>
          <line x1="${startX}" y1="${startY}" x2="${targetX}" y2="${targetY}" stroke="#dc2626" stroke-width="4" marker-end="url(#docs-callout-arrow)" />
          <rect x="${box.x - 4}" y="${box.y - 4}" width="${box.width + 8}" height="${box.height + 8}" rx="10" fill="none" stroke="#dc2626" stroke-width="3" />
        </svg>
        <div style="
          position:absolute;
          left:${bubbleX}px;
          top:${bubbleY}px;
          width:${bubbleWidth}px;
          min-height:${bubbleHeight}px;
          box-sizing:border-box;
          padding:10px 14px;
          border-radius:14px;
          color:white;
          background:#b91c1c;
          box-shadow:0 14px 34px rgba(15, 23, 42, 0.26);
          font-size:15px;
          font-weight:800;
          line-height:1.15;
        ">${label}</div>
      `;
      document.body.appendChild(layer);
    },
    { box, label, side },
  );
}

export async function holdCallout(
  page: Page,
  target: Locator,
  label: string,
  side: CalloutSide = 'left',
  duration = 1000,
) {
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      await expect(target.first()).toBeVisible({ timeout: 10_000 });
      await target.first().scrollIntoViewIfNeeded({ timeout: 10_000 });
      await addCallout(page, target, label, side);
      break;
    } catch (error) {
      if (attempt === 2) throw error;
      await page.waitForTimeout(400);
    }
  }
  await page.waitForTimeout(duration);
  await clearCallouts(page);
}

async function moveTo(page: Page, target: Locator) {
  await target.first().scrollIntoViewIfNeeded({ timeout: 10_000 });
  const box = await target.first().boundingBox();
  if (!box) return;
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2, {
    steps: 24,
  });
}

export async function smoothClick(page: Page, target: Locator) {
  await expect(target.first()).toBeVisible({ timeout: 10_000 });
  await moveTo(page, target);
  await page.waitForTimeout(250);
  await target.first().click();
  await page.waitForTimeout(650);
}

export async function smoothFill(page: Page, target: Locator, value: string) {
  await expect(target.first()).toBeVisible({ timeout: 10_000 });
  await moveTo(page, target);
  await page.waitForTimeout(200);
  await target.first().click();
  await page.keyboard.press(process.platform === 'darwin' ? 'Meta+A' : 'Control+A');
  await page.keyboard.type(value, { delay: 30 });
  await page.waitForTimeout(250);
}
