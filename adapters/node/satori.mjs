// satori (the engine behind @vercel/og): JSX-like tree -> SVG, rasterised with resvg like @vercel/og does.
import satori from 'satori';
import { Resvg } from '@resvg/resvg-js';
import { readConfig, runFixtures, pkgVersion, geometry } from './_lib.mjs';

const config = readConfig();
await runFixtures(config, pkgVersion('satori'), async (fixture) => {
  const g = geometry(config, fixture);
  const element = {
    type: 'div',
    props: {
      dir: fixture.dir,
      style: {
        display: 'flex', width: '100%', height: '100%', background: '#fff', color: '#000',
        fontFamily: 'DejaVu', fontSize: config.fontSize, padding: g.pad,
        justifyContent: 'flex-end', direction: fixture.dir,
      },
      children: fixture.wrap
        ? { type: 'div', props: { style: { width: config.wrapWidth, textAlign: 'right' }, children: fixture.text } }
        : fixture.text,
    },
  };
  const svg = await satori(element, {
    width: g.width, height: g.height,
    fonts: [{ name: 'DejaVu', data: config.fontBytes, weight: 400, style: 'normal' }],
  });
  const png = new Resvg(svg, { fitTo: { mode: 'zoom', value: config.scale } }).render().asPng();
  return { ext: 'png', data: png };
});
