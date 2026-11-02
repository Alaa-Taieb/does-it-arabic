// Chart.js 4 rendered server-side on @napi-rs/canvas: a chart whose title is the fixture text
// (axes, legend and data hidden so only the chart library's text drawing is judged).
import { createCanvas, GlobalFonts } from '@napi-rs/canvas';
import { Chart, BarController, BarElement, CategoryScale, LinearScale, Title } from 'chart.js';
import { readConfig, runFixtures, pkgVersion, geometry } from './_lib.mjs';

Chart.register(BarController, BarElement, CategoryScale, LinearScale, Title);
const config = readConfig();
GlobalFonts.registerFromPath(config.fontPath, 'DejaVu');

const whiteBackground = {
  id: 'white',
  beforeDraw: (c) => {
    c.ctx.save();
    c.ctx.fillStyle = '#fff';
    c.ctx.fillRect(0, 0, c.width, c.height);
    c.ctx.restore();
  },
};

await runFixtures(config, pkgVersion('chart.js'), async (fixture) => {
  if (fixture.wrap) return { skip: 'chart titles do not wrap automatically' };
  const g = geometry(config, fixture);
  const canvas = createCanvas(g.width, g.height + 40);
  const chart = new Chart(canvas, {
    type: 'bar',
    data: { labels: [], datasets: [] },
    options: {
      responsive: false,
      animation: false,
      devicePixelRatio: config.scale,
      scales: { x: { display: false }, y: { display: false } },
      plugins: {
        legend: { display: false },
        title: { display: true, text: fixture.text, color: '#000', font: { family: 'DejaVu', size: config.fontSize } },
      },
    },
    plugins: [whiteBackground],
  });
  const png = await canvas.encode('png');
  chart.destroy();
  return { ext: 'png', data: png };
});
