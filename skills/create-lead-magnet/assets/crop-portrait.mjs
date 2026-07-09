#!/usr/bin/env node
// crop-portrait.mjs — extract a clean single headshot from a creator's identity
// plate (which is a turnaround sheet: front headshot on top, 3/4 + profile below).
// Cropping is a NON-GENERATIVE transform — no new generation approval is needed.
// NEVER generate a new face for the lead magnet; always reuse the APPROVED plate.
//
//   node crop-portrait.mjs <identity-plate.png> <out-portrait.png> [topFraction=0.56]
//
// Uses headless Chrome via puppeteer-core (no Pillow/ImageMagick dependency).
// The plate is embedded as a base64 data URI because headless Chrome blocks
// file:// image loads from a setContent page.

import puppeteer from 'puppeteer-core';
import { readFileSync } from 'node:fs';
import { execSync } from 'node:child_process';

const [plate, out, topFrac = '0.56'] = process.argv.slice(2);
if (!plate || !out) { console.error('usage: crop-portrait.mjs <plate.png> <out.png> [topFraction]'); process.exit(1); }

function findChrome() {
  for (const c of [process.env.CHROME_PATH,
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium'].filter(Boolean)) {
    try { readFileSync(c); return c; } catch {}
  }
  throw new Error('Set CHROME_PATH to a Chrome/Chromium binary.');
}
// dimensions via sips (macOS) — swap for any dims tool on other platforms
const W = +execSync(`sips -g pixelWidth "${plate}"`).toString().match(/pixelWidth:\s*(\d+)/)[1];
const H = +execSync(`sips -g pixelHeight "${plate}"`).toString().match(/pixelHeight:\s*(\d+)/)[1];
const cropH = Math.round(H * parseFloat(topFrac));

const b64 = readFileSync(plate).toString('base64');
const browser = await puppeteer.launch({ executablePath: findChrome(), headless: true, args: ['--no-sandbox'] });
try {
  const page = await browser.newPage();
  await page.setViewport({ width: W, height: cropH, deviceScaleFactor: 1 });
  await page.setContent(`<style>*{margin:0;padding:0}</style><img id="i" src="data:image/png;base64,${b64}" style="display:block;width:${W}px">`);
  await page.evaluate(() => new Promise(r => { const im = document.getElementById('i'); im.complete && im.naturalWidth ? r() : (im.onload = r); }));
  await page.screenshot({ path: out, clip: { x: 0, y: 0, width: W, height: cropH } });
  console.log(`cropped ${W}x${cropH} -> ${out}`);
} finally {
  await browser.close();
}
