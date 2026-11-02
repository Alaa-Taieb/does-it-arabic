// @napi-rs/canvas (Skia): the HTML canvas API in Node, used for OG images. Sets ctx.direction.
import { createCanvas, GlobalFonts } from '@napi-rs/canvas';
import { readConfig, runFixtures, pkgVersion, geometry } from './_lib.mjs';

const config = readConfig();
GlobalFonts.registerFromPath(config.fontPath, 'DejaVu');

await runFixtures(config, pkgVersion('@napi-rs/canvas'), async (fixture) => {
  if (fixture.wrap) return { skip: 'the canvas API has no line wrapping' };
  const g = geometry(config, fixture);
  const s = config.scale;
  const canvas = createCanvas(g.width * s, g.height * s);
  const ctx = canvas.getContext('2d');
  ctx.scale(s, s);
  ctx.fillStyle = '#fff';
  ctx.fillRect(0, 0, g.width, g.height);
  ctx.fillStyle = '#000';
  ctx.font = `${config.fontSize}px DejaVu`;
  ctx.direction = fixture.dir;
  ctx.textAlign = 'right';
  ctx.textBaseline = 'top';
  ctx.fillText(fixture.text, g.width - g.pad, g.pad);
  return { ext: 'png', data: await canvas.encode('png') };
});
