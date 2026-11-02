// Headless Chrome print-to-PDF (what developers fall back to): HTML with dir="rtl", page.pdf().
import { chromium } from 'playwright-core';
import { findChrome } from '../../reference/find-chrome.mjs';
import { readConfig, runFixtures, geometry } from './_lib.mjs';

const config = readConfig();
const browser = await chromium.launch({ executablePath: findChrome(), headless: true });
const page = await browser.newPage();
const fontUrl = `data:font/ttf;base64,${config.fontBytes.toString('base64')}`;
const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
try {
  await runFixtures(config, `Chrome ${browser.version()}`, async (fixture) => {
    const g = geometry(config, fixture);
    const width = fixture.wrap ? `width:${config.wrapWidth}px;` : 'white-space:nowrap;';
    await page.setContent(`<!doctype html><html lang="${fixture.lang}"><head><meta charset="utf-8"><style>
      @font-face { font-family: DejaVu; src: url('${fontUrl}'); }
      @page { size: ${g.width}px ${g.height}px; margin: 0; }
      body { margin: ${g.pad}px; font-family: DejaVu; font-size: ${config.fontSize}px; }
      p { margin: 0 0 0 auto; text-align: right; ${width} }
    </style></head><body><p dir="${fixture.dir}">${esc(fixture.text)}</p></body></html>`);
    await page.evaluate(() => document.fonts.ready);
    const data = await page.pdf({ width: `${g.width}px`, height: `${g.height}px`, printBackground: true });
    return { ext: 'pdf', data };
  });
} finally {
  await browser.close();
}
