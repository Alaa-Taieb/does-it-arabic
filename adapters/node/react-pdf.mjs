// @react-pdf/renderer: Font.register + <Text> with textAlign right, rendered to a buffer.
import React from 'react';
import { Document, Page, Text, Font, renderToBuffer } from '@react-pdf/renderer';
import { readConfig, runFixtures, pkgVersion, geometry } from './_lib.mjs';

const config = readConfig();
Font.register({ family: 'DejaVu', src: config.fontPath });
const h = React.createElement;

await runFixtures(config, pkgVersion('@react-pdf/renderer'), async (fixture) => {
  const g = geometry(config, fixture);
  const style = { fontFamily: 'DejaVu', fontSize: config.fontSize, textAlign: 'right' };
  if (fixture.wrap) Object.assign(style, { width: config.wrapWidth, marginLeft: g.width - 2 * g.pad - config.wrapWidth });
  const doc = h(Document, null,
    h(Page, { size: [g.width, g.height], style: { padding: g.pad, backgroundColor: '#fff' } },
      h(Text, { style }, fixture.text)));
  return { ext: 'pdf', data: await renderToBuffer(doc) };
});
