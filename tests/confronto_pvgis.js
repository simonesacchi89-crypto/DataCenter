// Confronto dei casi di SPEC §7: clima sintetico (Milano Linate, medie 1991–2020) contro anno tipo PVGIS.
// Uso: node tests/confronto_pvgis.js [--tmy]   (richiede i file in cache/pvgis/, scaricati dal backend)
const fs = require('node:fs');
const path = require('node:path');
const E = require('../engine.js');
const D = require('../dati.js');
const { calcolaCasi, verificaCasi } = require('../casi.js');

const ROOT = path.join(__dirname, '..');
const SITI = [
  ['Magenta (ex Novaceta)', '45.467_8.874'],
  ['Rho-Pero (AWS)', '45.510_9.087'],
  ['Milano Linate', '45.445_9.277'],
];

const sint = [];
for (let i = 0; i < 10; i++) sint.push(E.buildYear(D.CLIMI.milano, 2.5, 1000 + i * 7919));
const colonne = [['Sintetico Milano (10 anni)', calcolaCasi(sint)]];
const leggi = f => JSON.parse(fs.readFileSync(path.join(ROOT, 'cache', 'pvgis', f), 'utf8'));
const soloTMY = process.argv.includes('--tmy');
for (const [nome, k] of SITI) {
  const tmy = leggi(`tmy_${k}.json`).ore;
  const anni = soloTMY ? [E.hoursFromPVGIS(tmy)] : E.yearsFromPVGIS(tmy, leggi(`serie_${k}.json`));
  colonne.push([`PVGIS ${nome}${soloTMY ? ' (anno tipo)' : ' (19 anni)'}`, calcolaCasi(anni)]);
}

const f0 = x => Math.round(x).toLocaleString('it-IT');
const f2 = x => x.toFixed(2).replace('.', ',');
const f3 = x => x.toFixed(3).replace('.', ',');
const righe = [
  ['AWS acqua (m³) – pubbl. 50.000', r => f0(r.aws.acquaM3)],
  ['AWS PUE – pubbl. 1,08', r => f2(r.aws.pue)],
  ['Magenta chiller PUE annuo – obiettivo 1,25', r => f2(r.magentaDry.pue)],
  ['Magenta chiller PUE ora peggiore – picco 1,50', r => f2(r.magentaDry.pueOraPeggiore)],
  ['Magenta hybrid >25 °C (m³) – ~500.000', r => f0(r.magentaHybrid.acqua25)],
  ['Magenta hybrid >26 °C (m³) – ~500.000', r => f0(r.magentaHybrid.acqua26)],
  ['Magenta adiabatico >29 °C (m³) – ~200.000', r => f0(r.magentaAdiabatico.acquaM3)],
  ['Microsoft ore >29,4 °C – < 5%', r => `${f0(r.microsoft.oreSopra)} (${(r.microsoft.quotaOre * 100).toFixed(1).replace('.', ',')}%)`],
  ['Microsoft WUE – EMEA 0,03', r => f3(r.microsoft.wue)],
];

let md = '| Caso | ' + colonne.map(c => c[0]).join(' | ') + ' |\n|---|' + colonne.map(() => '---|').join('') + '\n';
for (const [nome, fn] of righe) md += `| ${nome} | ${colonne.map(c => fn(c[1])).join(' | ')} |\n`;
md += '\n**Esito verifiche (tolleranze SPEC §7)**\n\n| Verifica | ' + colonne.map(c => c[0]).join(' | ') + ' |\n|---|' + colonne.map(() => '---|').join('') + '\n';
const ver = colonne.map(c => verificaCasi(c[1]));
ver[0].forEach((v, i) => { md += `| ${v.caso} | ${ver.map(x => (x[i].ok ? '✅' : '❌')).join(' | ')} |\n`; });
console.log(md);
