// PDFKit: documented usage, registerFont + text(), right-aligned, wrapping via the width option.
import PDFDocument from 'pdfkit';
import { readConfig, runFixtures, pkgVersion, geometry } from './_lib.mjs';

const config = readConfig();
await runFixtures(config, pkgVersion('pdfkit'), (fixture) => new Promise((resolve, reject) => {
  const g = geometry(config, fixture);
  const doc = new PDFDocument({ size: [g.width, g.height], margin: 0 });
  const chunks = [];
  doc.on('data', (c) => chunks.push(c));
  doc.on('end', () => resolve({ ext: 'pdf', data: Buffer.concat(chunks) }));
  doc.on('error', reject);
  doc.registerFont('DejaVu', config.fontPath);
  doc.font('DejaVu').fontSize(config.fontSize);
  const width = fixture.wrap ? config.wrapWidth : g.width - 2 * g.pad;
  doc.text(fixture.text, g.pad, g.pad, { width, align: 'right', lineBreak: !!fixture.wrap });
  doc.end();
}));
