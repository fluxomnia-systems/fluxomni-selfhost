import type { Page } from '@playwright/test';

const TAILSCALE_HOST =
  /\b100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3}\b|\.ts\.net\b/i;
const SECRET =
  /-----BEGIN [A-Z ]*PRIVATE KEY-----|pk_[A-Za-z0-9]{8,}|\b100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3}\b|\.ts\.net\b|curl\s|FLX_[A-Z0-9_]{3,}=/i;

const SAFE_ENROLLMENT_URL = 'https://control.example.com/api/node-enrollment/redeem';
const SAFE_COMMAND = 'Generate a join command to install this node.';

/**
 * Removes one-time enrollment material, publish tokens, private keys, and
 * Tailscale-only hosts from the live DOM before a screenshot or video frame.
 */
export async function redactLabSecrets(page: Page) {
  await page.evaluate(
    ({ secretSource, tailscaleSource, safeUrl, safeCommand }) => {
      const secret = new RegExp(secretSource, 'i');
      const tailscale = new RegExp(tailscaleSource, 'i');

      const scrubValue = (value: string) => {
        if (!value || !secret.test(value) && !tailscale.test(value)) return value;
        if (/node-enrollment|https?:/i.test(value)) return safeUrl;
        return 'control.example.com';
      };

      const cover = (node: Element, label: string) => {
        const box = node.getBoundingClientRect();
        if (box.width < 2 || box.height < 2) return;
        const mask = document.createElement('div');
        mask.className = 'docs-secret-mask';
        mask.textContent = label;
        mask.style.position = 'fixed';
        mask.style.left = `${box.x}px`;
        mask.style.top = `${box.y}px`;
        mask.style.width = `${box.width}px`;
        mask.style.height = `${box.height}px`;
        mask.style.zIndex = '2147483646';
        mask.style.display = 'flex';
        mask.style.alignItems = 'center';
        mask.style.padding = '0 8px';
        mask.style.overflow = 'hidden';
        mask.style.background = '#111827';
        mask.style.color = '#e5e7eb';
        mask.style.font = '12px/1.2 ui-sans-serif, system-ui, sans-serif';
        document.body.appendChild(mask);
      };

      document.querySelectorAll('.docs-secret-mask').forEach((node) => node.remove());
      document.querySelectorAll('input, textarea').forEach((node) => {
        const field = node as HTMLInputElement;
        const next = scrubValue(field.value);
        if (next === field.value) return;
        field.value = next;
        cover(field, next);
      });

      document.querySelectorAll('details').forEach((details) => {
        const summary = details.querySelector('summary')?.textContent ?? '';
        if (!/recent enrollment codes/i.test(summary)) return;
        details.open = false;
        details.querySelectorAll('li').forEach((item) => item.remove());
      });

      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      let current = walker.nextNode();
      while (current) {
        const text = current.textContent ?? '';
        if (secret.test(text) || tailscale.test(text)) {
          current.textContent = safeCommand;
        }
        current = walker.nextNode();
      }
    },
    {
      secretSource: SECRET.source,
      tailscaleSource: TAILSCALE_HOST.source,
      safeUrl: SAFE_ENROLLMENT_URL,
      safeCommand: SAFE_COMMAND,
    },
  );
}
