// Casi di test di SPEC §7, calcolati su un insieme di anni orari qualsiasi
// (anni sintetici da medie mensili oppure anno tipo PVGIS). Parametri identici a calcolatore.html.
const E = typeof require !== 'undefined' ? require('./engine.js') : globalThis;
const D = typeof require !== 'undefined' ? require('./dati.js') : globalThis;

function calcolaCasi(years) {
  const { simulateMultiHours, hoursAboveHours, gridFactor } = E;
  const { SYS, COMMON0, MIX0, F0 } = D;
  const run = (p, extra) => simulateMultiHours(Object.assign({}, COMMON0, p, extra), years);

  const aws = run(SYS.diretta.p, { itMW: 79, load: 1 });
  const msP = { sys: 'direct', tSwitch: 29.4, tSup: 27, eps: 0.85, dTair: 12, coc: 3.5, fan: 0.03 };
  const ms = run(msP, { itMW: 10, load: 1 });
  const msHours = hoursAboveHours(years, 29.4);
  const mgDry = run(SYS.aria_dry.p, { itMW: 240, load: 1 });
  const mgHyb25 = run(SYS.torri.p, { tDry: 25, itMW: 240, load: 1 });
  const mgHyb26 = run(SYS.torri.p, { tDry: 26, itMW: 240, load: 1 });
  const mgAdia29 = run(SYS.aria_adiab.p, { tSwitch: 29, itMW: 240, load: 1 });
  const g = gridFactor(MIX0, F0, false), gh = gridFactor(MIX0, F0, true);

  return {
    aws: { acquaM3: aws.waterM3, pue: aws.pue },
    microsoft: { quotaOre: msHours / 8760, oreSopra: msHours, wue: ms.wue },
    magentaDry: { pue: mgDry.pue, pueOraPeggiore: mgDry.pueHourMax },
    magentaHybrid: { acqua25: mgHyb25.waterM3, acqua26: mgHyb26.waterM3 },
    magentaAdiabatico: { acquaM3: mgAdia29.waterM3 },
    rete: { fattore: g.factor, conBacini: gh.factor },
  };
}

// Verifiche con le tolleranze di SPEC §7. Ritorna [{caso, ok, valore, atteso}]
function verificaCasi(r) {
  const dev = (a, b) => Math.abs(a - b) / b;
  return [
    { caso: 'AWS Rho-Pero: acqua ±20% su 50.000 m³', ok: dev(r.aws.acquaM3, 50000) < 0.2, valore: r.aws.acquaM3, atteso: '40.000–60.000' },
    { caso: 'AWS Rho-Pero: PUE ~1,08', ok: Math.abs(r.aws.pue - 1.08) < 0.02, valore: r.aws.pue, atteso: '1,06–1,10' },
    { caso: 'Magenta chiller ad aria: PUE annuo 1,10–1,30', ok: r.magentaDry.pue >= 1.10 && r.magentaDry.pue <= 1.30, valore: r.magentaDry.pue, atteso: '1,10–1,30 (modello ~1,17)' },
    { caso: 'Magenta hybrid cooler: ±20% su 500.000 m³ (sopra 25 °C)', ok: dev(r.magentaHybrid.acqua25, 500000) < 0.2, valore: r.magentaHybrid.acqua25, atteso: '400.000–600.000' },
    { caso: 'Magenta hybrid cooler: ±20% su 500.000 m³ (sopra 26 °C)', ok: dev(r.magentaHybrid.acqua26, 500000) < 0.2, valore: r.magentaHybrid.acqua26, atteso: '400.000–600.000' },
    { caso: 'Magenta adiabatico: ±20% su 200.000 m³', ok: dev(r.magentaAdiabatico.acquaM3, 200000) < 0.2, valore: r.magentaAdiabatico.acquaM3, atteso: '160.000–240.000' },
    { caso: 'Microsoft: acqua < 5% delle ore', ok: r.microsoft.quotaOre < 0.05, valore: r.microsoft.quotaOre, atteso: '< 0,05' },
    { caso: 'Microsoft: WUE plausibile (0,03 ± 0,02)', ok: Math.abs(r.microsoft.wue - 0.03) < 0.02, valore: r.microsoft.wue, atteso: '0,01–0,05' },
    { caso: 'Rete Italia: ~0,67 L/kWh', ok: Math.abs(r.rete.fattore - 0.67) < 0.03, valore: r.rete.fattore, atteso: '0,64–0,70' },
    { caso: 'Rete Italia con bacini: ~2,9 L/kWh', ok: Math.abs(r.rete.conBacini - 2.9) < 0.15, valore: r.rete.conBacini, atteso: '2,75–3,05' },
  ];
}

if (typeof module !== 'undefined') module.exports = { calcolaCasi, verificaCasi };
