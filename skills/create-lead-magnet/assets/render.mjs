#!/usr/bin/env node
// Optional automated renderer. Manual Chrome Print -> Save as PDF needs no
// Node dependency; this helper requires puppeteer-core.
//
//   node render.mjs <input.html> <output.pdf>

import { resolve } from 'node:path';
import { loadPuppeteer } from './browser-runtime.mjs';
import { findChrome } from './chrome-paths.mjs';


const [input, output] = process.argv.slice(2);
if (!input || !output) {
  console.error('usage: render.mjs <input.html> <output.pdf>');
  process.exit(1);
}

const puppeteer = await loadPuppeteer();
const browser = await puppeteer.launch({
  executablePath: await findChrome(),
  headless: true,
  args: ['--no-sandbox', '--font-render-hinting=none'],
});

try {
  const page = await browser.newPage();
  await page.goto(`file://${resolve(input)}`, { waitUntil: 'networkidle0' });
  await page.evaluate(() => document.fonts.ready);
  await page.pdf({
    path: output,
    printBackground: true,
    preferCSSPageSize: true,
  });
  console.log(`rendered ${input} -> ${output}`);
} finally {
  await browser.close();
}
