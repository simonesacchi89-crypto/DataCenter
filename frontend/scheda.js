// Generatore della scheda di prefattibilità (Fase 4). Funzione pura: dati in ingresso → documento HTML stampabile.
// Usata dalla pagina e dai test (node). Nessun dato personale: solo particelle, fonti e calcoli.

const DISCLAIMER = 'Prefattibilità indicativa. Non sostituisce certificato di destinazione urbanistica, richiesta di connessione a Terna, indagini in sito né il parere di un tecnico abilitato.';

const LIMITI = [
  'La capacità di connessione la conosce solo Terna.',
  'La destinazione urbanistica vale solo con il certificato del comune.',
  'Il calcolo è una stima preliminare: per un progetto vero servono i dati dei costruttori (curve dei chiller, portate d\'aria, ricircoli).',
  'La superficie è quella grafica della mappa catastale e può differire da quella catastale ufficiale.',
  'I dati pubblici possono essere incompleti o non aggiornati: ogni criterio riporta fonte e data.',
];

// A chi rivolgere la domanda di ciascun criterio
const DESTINATARI = {
  1: 'Progettista', 2: 'Comune', 3: 'Soprintendenza e Comune', 4: 'Autorità di distretto e Comune', 5: 'Autorità di distretto e Comune',
  6: 'ARPA e Comune', 7: 'ARPA o indagini in sito', 8: 'Terna', 9: 'Terna', 10: 'Comune', 11: 'Ente gestore dell\'area protetta / Regione',
  12: 'Regione', 13: 'Comune o gestore del teleriscaldamento', 14: 'Progettista',
};
const ORDINE_DEST = ['Comune', 'Terna', 'Soprintendenza e Comune', 'ARPA e Comune', 'ARPA o indagini in sito', 'Autorità di distretto e Comune',
  'Ente gestore dell\'area protetta / Regione', 'Regione', 'Comune o gestore del teleriscaldamento', 'Progettista'];
const TXT = { verde: 'Verde', giallo: 'Giallo', rosso: 'Rosso', grigio: 'Da verificare', info: 'Informativo' };

function esc(t) { return String(t ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c])); }

// Domande: solo dai criteri gialli, rossi e grigi (SPEC §3). Se manca un testo, se ne genera uno generico.
function domande(criteri) {
  const per = {};
  for (const c of criteri) {
    if (!['giallo', 'rosso', 'grigio'].includes(c.stato)) continue;
    const testo = c.domanda || (c.stato === 'grigio'
      ? `${c.nome}: il dato non è disponibile in automatico. Verificarlo presso la fonte ufficiale.`
      : `${c.nome}: approfondire (${c.valore}).`);
    const d = DESTINATARI[c.id] || 'Altro';
    (per[d] = per[d] || []).push({ id: c.id, stato: c.stato, testo });
  }
  return ORDINE_DEST.filter(d => per[d]).map(d => ({ destinatario: d, domande: per[d] }))
    .concat(Object.keys(per).filter(d => !ORDINE_DEST.includes(d)).map(d => ({ destinatario: d, domande: per[d] })));
}

// Disegno SVG del lotto (senza sfondo cartografico, così funziona anche offline e in stampa)
function svgLotto(particelle, W = 520, H = 300) {
  const pts = particelle.flatMap(p => (p.geometry.type === 'Polygon' ? [p.geometry.coordinates] : p.geometry.coordinates).flatMap(poly => poly[0]));
  if (!pts.length) return '';
  const lat0 = pts.reduce((a, p) => a + p[1], 0) / pts.length;
  const kx = Math.cos(lat0 * Math.PI / 180) * 111320, ky = 111150;
  const xs = pts.map(p => p[0] * kx), ys = pts.map(p => p[1] * ky);
  const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
  const pad = 20, s = Math.min((W - 2 * pad) / (x1 - x0 || 1), (H - 2 * pad - 20) / (y1 - y0 || 1));
  const tx = x => pad + (x * kx - x0) * s, ty = y => H - pad - 20 - (y * ky - y0) * s;
  let out = `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="Disegno del lotto" xmlns="http://www.w3.org/2000/svg">`;
  for (const p of particelle) {
    const polys = p.geometry.type === 'Polygon' ? [p.geometry.coordinates] : p.geometry.coordinates;
    for (const poly of polys) {
      const d = poly.map(r => 'M' + r.map(c => `${tx(c[0]).toFixed(1)},${ty(c[1]).toFixed(1)}`).join('L') + 'Z').join('');
      out += `<path d="${d}" fill="#c4552a33" stroke="#c4552a" stroke-width="1.2" fill-rule="evenodd"/>`;
    }
    const r0 = polys[0][0], cx = r0.reduce((a, c) => a + c[0], 0) / r0.length, cy = r0.reduce((a, c) => a + c[1], 0) / r0.length;
    if (p.superficie_m2 > 1500) out += `<text x="${tx(cx).toFixed(1)}" y="${ty(cy).toFixed(1)}" font-size="10" text-anchor="middle" fill="#333">${esc(p.particella)}</text>`;
  }
  // barra di scala
  const metri = [50, 100, 200, 250, 500, 1000, 2000].find(m => m * s > 60) || 100;
  out += `<line x1="${pad}" y1="${H - 12}" x2="${pad + metri * s}" y2="${H - 12}" stroke="#333" stroke-width="2"/>`
    + `<text x="${pad + metri * s + 6}" y="${H - 8}" font-size="10" fill="#333">${metri} m</text>`
    + `<text x="${W - pad}" y="${H - 8}" font-size="10" text-anchor="end" fill="#333">N ↑</text></svg>`;
  return out;
}

// Confine delle particelle da sovrapporre a un'immagine WMS in EPSG:4326 (riquadro [s, w, n, e], proporzione lineare)
function svgSovrapposto(particelle, riquadro, W, H) {
  const [s, w, n, e] = riquadro;
  const x = lon => ((lon - w) / (e - w) * W).toFixed(1), y = lat => ((n - lat) / (n - s) * H).toFixed(1);
  const paths = particelle.map(p => (p.geometry.type === 'Polygon' ? [p.geometry.coordinates] : p.geometry.coordinates)
    .map(poly => poly.map(r => 'M' + r.map(c => `${x(c[0])},${y(c[1])}`).join('L') + 'Z').join('')).join('')).join('');
  return `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg"><path d="${paths}" fill="none" stroke="#ff7a1a" stroke-width="${Math.max(2, W / 400)}" fill-rule="evenodd"/></svg>`;
}

function sezioneStatoSito(st) {
  if (!st || (!st.aerea && !(st.foto || []).length && !(st.note || []).length)) {
    return '<h2>Stato del sito (nota)</h2><p class="small">Nessuna foto o nota inserita. Consigliato un sopralluogo.</p>';
  }
  let h = '<h2>Stato del sito (nota, non semaforo)</h2>';
  if (st.aerea) {
    h += `<figure style="margin:6px 0"><div style="position:relative"><img src="${st.aerea.immagine}" alt="Foto aerea del lotto" style="width:100%;display:block">`
      + `<div style="position:absolute;inset:0">${st.aerea.sovrapposto.replace('<svg ', '<svg style="width:100%;height:100%" ')}</div></div>`
      + `<figcaption class="small">${esc(st.aerea.fonte)} · volo: ${esc(st.aerea.date_volo || st.aerea.anno)} · in arancione il lotto. ${esc(st.aerea.nota)}</figcaption></figure>`;
  }
  if ((st.note || []).length) h += `<div class="kv">${st.note.map(n => `<span>${esc(n.titolo)}</span><span style="color:inherit">${esc(n.testo)}</span>`).join('')}</div><p class="small">Note inserite a mano.</p>`;
  if ((st.foto || []).length) {
    h += `<div class="foto">${st.foto.map(f => `<figure><img src="${f.src}" alt="${esc(f.didascalia)}"><figcaption><b>${esc(f.didascalia)}</b><br><span class="small">${esc(f.fonte)}</span></figcaption></figure>`).join('')}</div>`;
  }
  return h;
}

function fmtN(x, d = 0) {
  if (x == null || isNaN(x)) return '–';
  return Number(x).toLocaleString('it-IT', { minimumFractionDigits: d, maximumFractionDigits: d, useGrouping: 'always' });
}

// d: { progetto:{nome,itMW,carico,sistema,clima}, sito:{comune,particelle[],superficie_m2,centro:{lat,lon},fonte,consultato_il},
//      criteri:[{id,nome,stato,valore,fonte,data_fonte,consultato_il,nota,domanda}], calcolo:{...}, data }
function costruisciScheda(d) {
  const crit = [...d.criteri].sort((a, b) => a.id - b.id);
  const conta = s => crit.filter(c => c.stato === s).length;
  const dom = domande(crit);
  const c = d.calcolo || {};
  const parts = d.sito.particelle || [];
  const fogli = [...new Set(parts.filter(p => !p.perimetro).map(p => p.foglio))].sort((a, b) => a - b);
  const perimetri = parts.filter(p => p.perimetro);
  const elencoPart = fogli.map(f => `foglio ${f}: ${parts.filter(p => p.foglio === f).map(p => p.particella)
    .sort((a, b) => (parseInt(a, 10) || 0) - (parseInt(b, 10) || 0)).join(', ')}`).concat(perimetri.map(p => `${p.particella} disegnato a mano`)).join(' · ');
  const fonti = [...new Map(crit.filter(x => x.fonte && !/a mano|^engine\.js/.test(x.fonte))
    .map(x => [x.fonte.replace(/ \(proposto, modificabile\)$/, ''), x])).entries()].map(([fonte, x]) => ({ fonte, url: x.url }));
  const dataIt = iso => iso ? new Date(iso).toLocaleDateString('it-IT') : '';

  return `<!doctype html>
<html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Scheda di prefattibilità – ${esc(d.progetto.nome)}</title>
<style>
  :root { --fg:#13222c; --muted:#566a77; --line:#d4dee4; --verde:#1a8a4a; --giallo:#f2c230; --rosso:#c8262b; --grigio:#7a8a94; --info:#1d6a96; }
  * { box-sizing: border-box; }
  body { font-family: "Segoe UI", Roboto, Arial, sans-serif; color: var(--fg); background: #fff; margin: 0; padding: 24px 16px; font-size: 13px; line-height: 1.45; }
  main { max-width: 820px; margin: 0 auto; }
  h1 { font-size: 22px; margin: 0 0 4px; } h2 { font-size: 15px; margin: 22px 0 8px; border-bottom: 2px solid var(--fg); padding-bottom: 3px; }
  .meta { color: var(--muted); font-size: 12px; }
  .avviso { border: 2px solid var(--rosso); padding: 8px 10px; margin: 12px 0; font-weight: 600; }
  table { width: 100%; border-collapse: collapse; } th, td { text-align: left; padding: 5px 6px; border-bottom: 1px solid var(--line); vertical-align: top; }
  th { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: .03em; }
  .sem { display: inline-block; min-width: 86px; text-align: center; padding: 1px 6px; border-radius: 10px; color: #fff; font-size: 11px; font-weight: 700;
         -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .verde { background: var(--verde); } .giallo { background: var(--giallo); color: #222; } .rosso { background: var(--rosso); } .grigio { background: var(--grigio); } .info { background: var(--info); }
  .riep { display: flex; gap: 10px; flex-wrap: wrap; margin: 6px 0; }
  .kv { display: grid; grid-template-columns: max-content 1fr; gap: 3px 14px; }
  .kv span { color: var(--muted); }
  .small { font-size: 11px; color: var(--muted); }
  .num { font-family: Consolas, Menlo, monospace; white-space: nowrap; }
  ol.dom { margin: 4px 0 10px 18px; padding: 0; } ol.dom li { margin-bottom: 3px; }
  .lotto { border: 1px solid var(--line); margin: 8px 0; }
  .foto { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 8px; } .foto figure { margin: 0; break-inside: avoid; } .foto img { width: 100%; display: block; }
  figure { break-inside: avoid; }
  @media print { body { padding: 0; } h2 { break-after: avoid; } tr, li { break-inside: avoid; } @page { margin: 14mm 12mm; } }
</style></head>
<body><main>
<div class="meta">PASSAPORTO ACQUA E CALORE · SCHEDA DI PREFATTIBILITÀ · ${esc(dataIt(d.data))}</div>
<h1>${esc(d.progetto.nome)}</h1>
<div class="avviso">${DISCLAIMER}</div>

<h2>Riepilogo</h2>
<div class="riep">
  <span><span class="sem verde">Verde</span> ${conta('verde')}</span>
  <span><span class="sem giallo">Giallo</span> ${conta('giallo')}</span>
  <span><span class="sem rosso">Rosso</span> ${conta('rosso')}</span>
  <span><span class="sem grigio">Da verificare</span> ${conta('grigio')}</span>
  ${conta('info') ? `<span><span class="sem info">Informativo</span> ${conta('info')}</span>` : ''}
</div>
${conta('rosso') ? `<p><b>Criteri rossi:</b> ${crit.filter(x => x.stato === 'rosso').map(x => esc(x.nome)).join('; ')}.</p>` : ''}
<p>Domande da fare: <b>${dom.reduce((a, g) => a + g.domande.length, 0)}</b>, rivolte a ${dom.length} interlocutori (elenco in fondo).</p>

<h2>Sito</h2>
<div class="kv">
  <span>Comune</span><b>${esc(d.sito.comune || '–')}</b>
  <span>Particelle</span><span style="color:inherit">${esc(elencoPart || '–')} (${parts.length})</span>
  <span>Superficie</span><b class="num">${fmtN(d.sito.superficie_m2)} m² (${fmtN(d.sito.superficie_m2 / 10000, 2)} ha)</b>
  <span>Centro del lotto</span><span style="color:inherit" class="num">${d.sito.centro ? `${d.sito.centro.lat.toFixed(5)}, ${d.sito.centro.lon.toFixed(5)}` : '–'}</span>
</div>
<div class="lotto">${svgLotto(parts)}</div>
<div class="small">Confini: ${esc(d.sito.fonte || '')}${d.sito.aggiornato ? ' · fogli aggiornati al ' + esc(d.sito.aggiornato) : ''}${d.sito.consultato_il ? ' · consultato il ' + esc(dataIt(d.sito.consultato_il)) : ''}. Superficie grafica, non catastale ufficiale. Nessun dato sui proprietari.</div>

${sezioneStatoSito(d.stato_sito)}

<h2>Ipotesi di progetto</h2>
<div class="kv">
  <span>Potenza IT</span><b class="num">${fmtN(d.progetto.itMW, 1)} MW</b>
  <span>Carico medio</span><b class="num">${fmtN(d.progetto.carico * 100)}%</b>
  <span>Raffreddamento</span><b>${esc(d.progetto.sistema)}</b>
  <span>Clima</span><span style="color:inherit">${esc(d.progetto.clima)}</span>
  ${d.progetto.energiaDichiarata ? `<span>Energia dichiarata</span><b class="num">${fmtN(d.progetto.energiaDichiarata, 1)} GWh/anno</b>` : ''}
</div>

<h2>Criteri</h2>
<table><thead><tr><th>Semaforo</th><th>#</th><th>Criterio</th><th>Valore trovato</th><th>Fonte e data</th><th>Nota</th></tr></thead><tbody>
${crit.map(x => `<tr><td><span class="sem ${x.stato}">${TXT[x.stato] || x.stato}</span></td><td>${x.id}</td><td>${esc(x.nome)}</td><td>${esc(x.valore)}</td>
<td class="small">${esc(x.fonte || '–')}${x.data_fonte ? '<br>dati: ' + esc(x.data_fonte) : ''}${x.consultato_il ? '<br>consultato il ' + esc(dataIt(x.consultato_il)) : ''}</td>
<td class="small">${esc(x.nota || '')}${x.dettagli && x.dettagli.length ? '<br>' + x.dettagli.slice(0, 5).map(esc).join('<br>') : ''}</td></tr>`).join('\n')}
</tbody></table>

<h2>Energia, acqua e calore</h2>
<table><tbody>
<tr><td>PUE (efficienza energetica)</td><td class="num"><b>${fmtN(c.pue, 2)}</b> · classe ${esc(c.classePUE)}</td><td class="small">forbice ${fmtN(c.pueMin, 2)}–${fmtN(c.pueMax, 2)}; ora peggiore ${fmtN(c.pueOraPeggiore, 2)}</td></tr>
<tr><td>WUE (acqua in sito, etichetta UE)</td><td class="num"><b>${fmtN(c.wue, 3)} L/kWh</b> · classe ${esc(c.classeWUE)}</td><td class="small"></td></tr>
<tr><td>Energia IT / totale</td><td class="num">${fmtN(c.itGWh, 1)} / ${fmtN(c.totGWh, 1)} GWh/anno</td><td class="small"></td></tr>
<tr><td>Acqua diretta</td><td class="num"><b>${fmtN(c.acquaM3)} m³/anno</b></td><td class="small">forbice tra anni ${fmtN(c.acquaMin)}–${fmtN(c.acquaMax)} m³</td></tr>
${c.acquaM3 > 1 ? `<tr><td>Prelievo massimo orario</td><td class="num">${fmtN(c.piccoM3h, 1)} m³/h</td><td class="small">fonte dell'acqua: ${esc(c.fonteAcqua || 'non indicata')}</td></tr>` : ''}
<tr><td>Acqua indiretta (centrali elettriche)</td><td class="num">${fmtN(c.indirettaM3)} m³/anno</td><td class="small">rete ${fmtN(c.fattoreRete, 2)} L/kWh, mix Terna 2025, metodo The Green Grid; fuori dall'etichetta UE</td></tr>
<tr><td>Impronta idrica completa</td><td class="num">${fmtN(c.impronta, 2)} L/kWh IT</td><td class="small">${fmtN(c.quotaIndiretta * 100)}% dalle centrali</td></tr>
<tr><td>Calore di scarto</td><td class="num">${fmtN(c.caloreGWh, 1)} GWh termici/anno</td><td class="small">temperatura indicativa ${esc(c.temperaturaCalore)}</td></tr>
</tbody></table>
<div class="small">Motore di calcolo orario (engine.js) · ${esc(d.progetto.clima)}. Classi secondo la bozza dell'etichetta UE (A–G).</div>

<h2>Domande da fare</h2>
${dom.length ? dom.map(g => `<p><b>${esc(g.destinatario)}</b></p><ol class="dom">${g.domande.map(q => `<li><span class="sem ${q.stato}">${TXT[q.stato]}</span> ${esc(q.testo)} <span class="small">(criterio ${q.id})</span></li>`).join('')}</ol>`).join('') : '<p>Nessuna: tutti i criteri sono verdi o informativi.</p>'}

<h2>Limiti</h2>
<ul>${LIMITI.map(l => `<li>${esc(l)}</li>`).join('')}</ul>

<h2>Fonti</h2>
<ul class="small">${fonti.map(f => `<li>${esc(f.fonte)}${f.url ? ' – ' + esc(f.url) : ''}</li>`).join('')}
<li>Clima: ${esc(d.progetto.clima)}</li></ul>

<div class="avviso">${DISCLAIMER}</div>
<div class="small">Generata il ${esc(new Date(d.data).toLocaleString('it-IT'))} con Passaporto Acqua e Calore (strumento locale).</div>
</main></body></html>`;
}

if (typeof module !== 'undefined') module.exports = { costruisciScheda, domande, svgLotto, svgSovrapposto, DISCLAIMER, DESTINATARI };
