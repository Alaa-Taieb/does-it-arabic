// jsPDF: the library coding agents reach for first. Plain documented usage: embed a TTF, call text().
import { jsPDF } from 'jspdf';
import { readConfig, runFixtures, pkgVersion, geometry } from './_lib.mjs';

const config = readConfig();
await runFixtures(config, pkgVersion('jspdf'), async (fixture) => {
  const g = geometry(config, fixture);
  const doc = new jsPDF({ unit: 'pt', format: [g.width, g.height], orientation: g.width > g.height ? 'l' : 'p' });
  doc.addFileToVFS('DejaVuSans.ttf', config.fontBytes.toString('base64'));
  doc.addFont('DejaVuSans.ttf', 'DejaVu', 'normal');
  doc.setFont('DejaVu', 'normal');
  doc.setFontSize(config.fontSize);
  const right = g.width - g.pad;
  if (fixture.wrap) {
    doc.text(doc.splitTextToSize(fixture.text, config.wrapWidth), right, g.pad + config.fontSize, { align: 'right' });
  } else {
    doc.text(fixture.text, right, g.pad + config.fontSize, { align: 'right' });
  }
  return { ext: 'pdf', data: Buffer.from(doc.output('arraybuffer')) };
});
