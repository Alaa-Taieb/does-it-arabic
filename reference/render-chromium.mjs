// Renders reference and synthetic-failure variants with Chromium (HarfBuzz shaping + full UBA).
// Usage: node reference/render-chromium.mjs <jobs.json> <font.ttf> <outdir>
// jobs.json: [{ "name": "invoice-line__ok", "text": "...", "dir": "rtl", "css": "...", "wrap": false }]
import { readFileSync, mkdirSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { chromium } from 'playwright-core';
import { findChrome } from './find-chrome.mjs';

const [jobsPath, fontPath, outDir] = process.argv.slice(2);
if (!jobsPath || !fontPath || !outDir) {
  console.error('usage: render-chromium.mjs <jobs.json> <font.ttf> <outdir>');
  process.exit(2);
}
const { fontSize, wrapWidth, scale, jobs } = JSON.parse(readFileSync(jobsPath, 'utf8'));
mkdirSync(outDir, { recursive: true });

const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
// Embed the font: Chromium blocks file:// fonts from an about:blank page.
const fontUrl = `data:font/ttf;base64,${readFileSync(resolve(fontPath)).toString('base64')}`;

const browser = await chromium.launch({ executablePath: findChrome(), headless: true });
const page = await browser.newPage({ deviceScaleFactor: scale });
const results = [];
for (const job of jobs) {
  const width = job.wrap ? `width:${wrapWidth}px;` : 'white-space:nowrap;display:inline-block;';
  const html = `<!doctype html><html><head><meta charset="utf-8"><style>
    @font-face { font-family: Fixture; src: url('${fontUrl}'); }
    html, body { margin: 0; background: #fff; }
    #t { font-family: Fixture; font-size: ${fontSize}px; color: #000; padding: 16px; ${width} ${job.css || ''} }
  </style></head><body><div id="t" dir="${job.dir}">${esc(job.text)}</div></body></html>`;
  await page.setContent(html, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  const file = join(outDir, `${job.name}.png`);
  await page.locator('#t').screenshot({ path: file });
  results.push({ name: job.name, file });
}
const version = browser.version();
await browser.close();
console.log(JSON.stringify({ renderer: 'chromium', version, results }));
