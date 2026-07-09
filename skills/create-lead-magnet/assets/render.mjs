#!/usr/bin/env node
// OPTIONAL render helper. The template is plain HTML/CSS — you do NOT need this.
// Zero-dependency path: open lead-magnet.html in Chrome → Print → Save as PDF
// (Margins: None, Background graphics: ON).
//
// This script is here only for automated/batch rendering:
//   npm i puppeteer-core          # once (reuses your installed Chrome)
//   node render.mjs lead-magnet.html samples/mara-vale.pdf
//
// The four settings below are what make HTML→PDF look right; keep them.

import { access } from 'node:fs/promises';
import { resolve } from 'node:path';

const [input = 'lead-magnet.html', output = 'out.pdf'] = process.argv.slice(2);

async function findChrome() {
  const candidates = [
    process.env.CHROME_PATH,
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
  ].filter(Boolean);
  for (const c of candidates) { try { await access(c); return c; } catch {} }
  throw new Error('Set CHROME_PATH to a Chrome/Chromium binary.');
}

const { default: puppeteer } = await import('puppeteer-core');
const browser = await puppeteer.launch({
  executablePath: await findChrome(),
  headless: true,
  args: ['--no-sandbox', '--font-render-hinting=none'],
});
try {
  const page = await browser.newPage();
  await page.goto('file://' + resolve(input), { waitUntil: 'networkidle0' });
  await page.evaluate(() => document.fonts.ready);   // wait for webfonts
  await page.pdf({
    path: output,
    printBackground: true,        // colour blocks / dark pages
    preferCSSPageSize: true,      // honour @page { size: Letter; margin: 0 }
  });
  console.log(`✓ ${input} → ${output}`);
} finally {
  await browser.close();
}
