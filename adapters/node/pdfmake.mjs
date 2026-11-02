// pdfmake (server build): register the TTF with setFonts, one right-aligned paragraph.
import { createRequire } from 'node:module';
import { readConfig, runFixtures, pkgVersion, geometry } from './_lib.mjs';

const require = createRequire(import.meta.url);
const pdfmake = require('pdfmake');
const config = readConfig();
const f = config.fontPath;
pdfmake.setFonts({ DejaVu: { normal: f, bold: f, italics: f, bolditalics: f } });
pdfmake.setLocalAccessPolicy(() => true);

await runFixtures(config, pkgVersion('pdfmake'), async (fixture) => {
  const g = geometry(config, fixture);
  const block = fixture.wrap
    ? { text: fixture.text, alignment: 'right', margin: [g.width - 2 * g.pad - config.wrapWidth, 0, 0, 0] }
    : { text: fixture.text, alignment: 'right', noWrap: true };
  const doc = pdfmake.createPdf({
    pageSize: { width: g.width, height: g.height },
    pageMargins: [g.pad, g.pad, g.pad, g.pad],
    defaultStyle: { font: 'DejaVu', fontSize: config.fontSize },
    content: [block],
  });
  return { ext: 'pdf', data: await doc.getBuffer() };
});
