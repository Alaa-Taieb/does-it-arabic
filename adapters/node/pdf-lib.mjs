// pdf-lib: embed the TTF through @pdf-lib/fontkit, drawText() right-aligned; maxWidth for wrapping.
import { PDFDocument, rgb } from 'pdf-lib';
import fontkit from '@pdf-lib/fontkit';
import { readConfig, runFixtures, pkgVersion, geometry } from './_lib.mjs';

const config = readConfig();
await runFixtures(config, pkgVersion('pdf-lib'), async (fixture) => {
  const g = geometry(config, fixture);
  const pdf = await PDFDocument.create();
  pdf.registerFontkit(fontkit);
  const font = await pdf.embedFont(config.fontBytes);
  const page = pdf.addPage([g.width, g.height]);
  const size = config.fontSize;
  const y = g.height - g.pad - size;
  if (fixture.wrap) {
    // pdf-lib has no text alignment option; wrapped lines start at x.
    page.drawText(fixture.text, { x: g.pad, y, size, font, color: rgb(0, 0, 0), maxWidth: config.wrapWidth, lineHeight: size * 1.2 });
  } else {
    const x = g.width - g.pad - font.widthOfTextAtSize(fixture.text, size);
    page.drawText(fixture.text, { x, y, size, font, color: rgb(0, 0, 0) });
  }
  return { ext: 'pdf', data: await pdf.save() };
});
