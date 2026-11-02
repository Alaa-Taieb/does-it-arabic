'use strict';
// arabic-fixtures: RTL test strings for Arabic, Persian and Hebrew document rendering.
const data = require('./fixtures.json');

/** All fixtures: [{ id, title, script, lang, dir, text, meaning, checks, wrap? }] */
const fixtures = data.fixtures;

/** Fixture ids in canonical order. */
function ids() {
  return fixtures.map((f) => f.id);
}

/** One fixture by id; throws on an unknown id. */
function get(id) {
  const f = fixtures.find((x) => x.id === id);
  if (!f) throw new Error(`unknown fixture "${id}"; known: ${ids().join(', ')}`);
  return f;
}

module.exports = { fixtures, ids, get, fontSize: data.fontSize, wrapWidth: data.wrapWidth, version: data.version };
