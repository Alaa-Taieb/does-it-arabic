// Workaround commonly suggested for jsPDF: pre-shape with arabic-persian-reshaper, reorder with
// bidi-js (Unicode Bidi Algorithm), then hand jsPDF a visual-order string.
import { jsPDF } from 'jspdf';
import { createRequire } from 'node:module';
import bidiFactory from 'bidi-js';
import { readConfig, runFixtures, pkgVersion, geometry } from './_lib.mjs';

const require = createRequire(import.meta.url);
const reshaper = require('arabic-persian-reshaper');
const bidi = bidiFactory();
const config = readConfig();

function visual(text, dir) {
  const shaped = reshaper.ArabicShaper.convertArabic(text);
  const levels = bidi.getEmbeddingLevels(shaped, dir);
  return bidi.getReorderedString(shaped, levels);
}

const version = `${pkgVersion('jspdf')} + arabic-persian-reshaper ${pkgVersion('arabic-persian-reshaper')} + bidi-js ${pkgVersion('bidi-js')}`;
await runFixtures(config, version, async (fixture) => {
  const g = geometry(config, fixture);
  const doc = new jsPDF({ unit: 'pt', format: [g.width, g.height], orientation: g.width > g.height ? 'l' : 'p' });
  doc.addFileToVFS('DejaVuSans.ttf', config.fontBytes.toString('base64'));
  doc.addFont('DejaVuSans.ttf', 'DejaVu', 'normal');
  doc.setFont('DejaVu', 'normal');
  doc.setFontSize(config.fontSize);
  const right = g.width - g.pad;
  if (fixture.wrap) {
    // Wrap the logical text first, then convert each line: reordering before wrapping puts the last words on line one.
    const lines = doc.splitTextToSize(fixture.text, config.wrapWidth).map((l) => visual(l, fixture.dir));
    doc.text(lines, right, g.pad + config.fontSize, { align: 'right' });
  } else {
    doc.text(visual(fixture.text, fixture.dir), right, g.pad + config.fontSize, { align: 'right' });
  }
  return { ext: 'pdf', data: Buffer.from(doc.output('arraybuffer')) };
});
