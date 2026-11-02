// Shared adapter plumbing. An adapter renders every fixture with one library and writes
// <outdir>/<fixtureId>.pdf|.png, then prints one JSON line: { version, outputs, errors, skipped }.
import { readFileSync, mkdirSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { join } from 'node:path';

const require = createRequire(import.meta.url);

export function pkgVersion(name) {
  try {
    // Resolve the package root through its package.json so "exports" maps do not get in the way.
    const entry = require.resolve(name);
    let dir = entry;
    for (let i = 0; i < 6; i++) {
      dir = join(dir, '..');
      try {
        const pkg = JSON.parse(readFileSync(join(dir, 'package.json'), 'utf8'));
        if (pkg.name === name) return pkg.version;
      } catch {}
    }
  } catch {}
  return 'unknown';
}

export function readConfig() {
  const [configPath, outDir] = process.argv.slice(2);
  if (!configPath || !outDir) {
    console.error('usage: <adapter> <config.json> <outdir>');
    process.exit(2);
  }
  const config = JSON.parse(readFileSync(configPath, 'utf8'));
  mkdirSync(outDir, { recursive: true });
  return { ...config, outDir, fontBytes: readFileSync(config.fontPath) };
}

/** Page geometry shared by all adapters, in the library's own unit (pt or px). */
export function geometry(config, fixture) {
  const pad = 20;
  if (fixture.wrap) return { width: config.wrapWidth + 2 * pad, height: 360, pad };
  return { width: 1000, height: 90, pad };
}

/**
 * Run render(fixture) for each fixture. render returns { ext, data } (Buffer/Uint8Array),
 * or { skip: 'reason' } when the library has no API for that fixture (e.g. no line wrapping).
 */
export async function runFixtures(config, version, render) {
  const outputs = {};
  const errors = {};
  const skipped = {};
  for (const fixture of config.fixtures) {
    try {
      const result = await render(fixture);
      if (result.skip) {
        skipped[fixture.id] = result.skip;
        continue;
      }
      const file = join(config.outDir, `${fixture.id}.${result.ext}`);
      writeFileSync(file, result.data);
      outputs[fixture.id] = file;
    } catch (err) {
      errors[fixture.id] = String(err && err.stack ? err.stack.split('\n').slice(0, 3).join(' | ') : err);
    }
  }
  console.log(JSON.stringify({ version, outputs, errors, skipped }));
}
