#!/usr/bin/env node
// Crop a user-reviewed rectangle from an approved identity plate. This is a
// non-generative transform; it never guesses the plate layout.
//
//   node crop-portrait.mjs <plate.png> <out.png> <x> <y> <width> <height>

import { readFile } from 'node:fs/promises';
import { loadPuppeteer } from './browser-runtime.mjs';
import { findChrome } from './chrome-paths.mjs';


const [plate, output, ...rectangleArgs] = process.argv.slice(2);
const rectangle = rectangleArgs.map(Number);
if (!plate || !output || rectangle.length !== 4 || rectangle.some((value) => !Number.isFinite(value))) {
  console.error('usage: crop-portrait.mjs <plate.png> <out.png> <x> <y> <width> <height>');
  process.exit(1);
}

const [x, y, width, height] = rectangle;
if (x < 0 || y < 0 || width <= 0 || height <= 0) {
  console.error('crop rectangle requires x/y >= 0 and width/height > 0');
  process.exit(1);
}

const plateBytes = await readFile(plate);
const dataUri = `data:image/png;base64,${plateBytes.toString('base64')}`;
const puppeteer = await loadPuppeteer();
const browser = await puppeteer.launch({
  executablePath: await findChrome(),
  headless: true,
  args: ['--no-sandbox'],
});

try {
  const page = await browser.newPage();
  await page.setViewport({ width: x + width, height: y + height, deviceScaleFactor: 1 });
  await page.setContent(
    `<style>*{margin:0;padding:0}</style><img id="plate" src="${dataUri}" style="display:block">`,
  );
  const dimensions = await page.evaluate(() => new Promise((resolveImage, rejectImage) => {
    const image = document.getElementById('plate');
    const done = () => resolveImage({ width: image.naturalWidth, height: image.naturalHeight });
    if (image.complete && image.naturalWidth) done();
    else {
      image.onload = done;
      image.onerror = () => rejectImage(new Error('identity plate could not be decoded'));
    }
  }));
  if (x + width > dimensions.width || y + height > dimensions.height) {
    throw new Error(
      `crop rectangle ${x},${y},${width},${height} exceeds plate ${dimensions.width}x${dimensions.height}`,
    );
  }
  await page.screenshot({ path: output, clip: { x, y, width, height } });
  console.log(`cropped ${x},${y},${width},${height} -> ${output}`);
} finally {
  await browser.close();
}
