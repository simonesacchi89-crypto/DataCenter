// Test del motore con il clima sintetico (come calcolatore.html): node --test tests/
const test = require('node:test');
const assert = require('node:assert');
const path = require('node:path');
const E = require(path.join(__dirname, '..', 'engine.js'));
const D = require(path.join(__dirname, '..', 'dati.js'));
const { calcolaCasi, verificaCasi } = require(path.join(__dirname, '..', 'casi.js'));

// Stessa costruzione degli anni usata nel calcolatore: Milano, sd 2,5, 10 anni
const SD = 2.5, N = 10;
const anni = [];
for (let i = 0; i < N; i++) anni.push(E.buildYear(D.CLIMI.milano, SD, 1000 + i * 7919));
const r = calcolaCasi(anni);

for (const v of verificaCasi(r)) {
  test(`clima sintetico Milano – ${v.caso}`, () => {
    assert.ok(v.ok, `valore ${v.valore}, atteso ${v.atteso}`);
  });
}

test('simulateMulti e simulateMultiHours danno lo stesso risultato', () => {
  const p = Object.assign({}, D.COMMON0, D.SYS.diretta.p, { itMW: 79, load: 1 });
  const a = E.simulateMulti(p, D.CLIMI.milano, SD, N);
  const b = E.simulateMultiHours(p, anni);
  assert.strictEqual(a.waterM3, b.waterM3);
  assert.strictEqual(a.pue, b.pue);
});

test('hoursFromPVGIS: mese, umidità limitata, bulbo umido ≤ temperatura', () => {
  const h = E.hoursFromPVGIS([
    { 'time(UTC)': '20180715:1300', T2m: 33.0, RH: 40 },
    { 'time(UTC)': '20160101:0000', T2m: -0.2, RH: 104 },
  ]);
  assert.strictEqual(h[0].m, 6);
  assert.strictEqual(h[1].m, 0);
  assert.strictEqual(h[1].RH, 100);
  assert.ok(h[0].Twb < h[0].T && h[0].Twb > 20 && h[0].Twb < 23);
});
