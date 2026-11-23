// Test del generatore della scheda (Fase 4): node --test tests/scheda.test.js
const test = require('node:test');
const assert = require('node:assert');
const path = require('node:path');
const { costruisciScheda, domande, DISCLAIMER } = require(path.join(__dirname, '..', 'frontend', 'scheda.js'));

const quadrato = { type: 'Polygon', coordinates: [[[8.87, 45.46], [8.872, 45.46], [8.872, 45.462], [8.87, 45.462], [8.87, 45.46]]] };
const dati = {
  data: '2026-11-23T10:00:00Z',
  progetto: { nome: 'Prova <Magenta>', itMW: 240, carico: 1, sistema: 'Chiller ad aria', clima: '19 anni reali PVGIS' },
  sito: { comune: 'Magenta (MI)', particelle: [{ foglio: 4, particella: '211', superficie_m2: 66262, geometry: quadrato }],
          superficie_m2: 66262, centro: { lat: 45.461, lon: 8.871 }, fonte: 'Agenzia delle Entrate', consultato_il: '2026-11-23T09:00:00Z' },
  criteri: [
    { id: 1, nome: 'Superficie per MW IT', stato: 'giallo', valore: '897 m²/MW', fonte: 'Catasto', domanda: 'Verificare la superficie.' },
    { id: 3, nome: 'Vincoli', stato: 'verde', valore: 'nessuno', fonte: 'SITAP', domanda: 'Domanda che NON deve comparire' },
    { id: 8, nome: 'Rete AT', stato: 'grigio', valore: 'da verificare', fonte: 'OpenStreetMap' },
    { id: 9, nome: 'Capacità', stato: 'giallo', valore: 'da chiedere', fonte: 'Terna', domanda: 'Chiedere a Terna la STMG.' },
    { id: 6, nome: 'Siti contaminati', stato: 'rosso', valore: 'bonifica aperta', fonte: 'inserito a mano', domanda: 'Chiedere ad ARPA.' },
    { id: 13, nome: 'Teleriscaldamento', stato: 'info', valore: 'nessuna rete', fonte: 'inserito a mano' },
  ],
  calcolo: { pue: 1.17, classePUE: 'B', wue: 0.006, classeWUE: 'A', acquaM3: 13035, indirettaM3: 2115273, caloreGWh: 2165.5 },
};

test('disclaimer presente in apertura e in chiusura', () => {
  const html = costruisciScheda(dati);
  assert.strictEqual(html.split(DISCLAIMER).length - 1, 2);
});

test('domande solo da gialli, rossi e grigi, raggruppate per destinatario', () => {
  const g = domande(dati.criteri);
  const tutte = g.flatMap(x => x.domande.map(d => d.id)).sort((a, b) => a - b);
  assert.deepStrictEqual(tutte, [1, 6, 8, 9]);
  const terna = g.find(x => x.destinatario === 'Terna');
  assert.deepStrictEqual(terna.domande.map(d => d.id), [8, 9]);
  assert.ok(terna.domande[0].testo.includes('non è disponibile'));  // grigio senza testo: domanda generica
});

test('nessuna domanda dai criteri verdi; testo con caratteri speciali protetto', () => {
  const html = costruisciScheda(dati);
  assert.ok(!html.includes('NON deve comparire'));
  assert.ok(html.includes('Prova &lt;Magenta&gt;') && !html.includes('Prova <Magenta>'));
});

test('ogni criterio con fonte, numeri principali e disegno del lotto', () => {
  const html = costruisciScheda(dati);
  for (const f of ['Catasto', 'SITAP', 'OpenStreetMap', 'Terna']) assert.ok(html.includes(f));
  assert.ok(html.includes('66.262 m²') && html.includes('13.035 m³/anno') && html.includes('<svg'));
  assert.ok(html.includes('La capacità di connessione la conosce solo Terna.'));
});
