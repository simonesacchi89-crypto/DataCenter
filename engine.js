// Motore di calcolo: data center, acqua diretta e indiretta, energia. Simulazione oraria su un anno tipo.
const HFG = 2430; // kJ/kg, calore latente di evaporazione dell'acqua a ~30 °C
const L_PER_KWH_HEAT = 3600 / HFG; // ~1,48 litri evaporati per kWh termico smaltito per evaporazione

const DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

function mulberry32(a) {
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
function gauss(rnd) {
  let u = 0, v = 0;
  while (u === 0) u = rnd();
  while (v === 0) v = rnd();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}
function svp(T) { return 6.112 * Math.exp((17.62 * T) / (243.12 + T)); } // hPa (Magnus)
function dewFromRH(T, RH) {
  const g = Math.log(RH / 100) + (17.62 * T) / (243.12 + T);
  return (243.12 * g) / (17.62 - g);
}
function rhFromDew(T, Td) { return Math.min(100, 100 * svp(Td) / svp(T)); }
function wetBulb(T, RH) { // Stull 2011
  return T * Math.atan(0.151977 * Math.sqrt(RH + 8.313659)) + Math.atan(T + RH) - Math.atan(RH - 1.676331)
    + 0.00391838 * Math.pow(RH, 1.5) * Math.atan(0.023101 * RH) - 4.686035;
}
function diurnal(h) { // 0 al minimo (ore 6), 1 al massimo (ore 15)
  if (h >= 6 && h <= 15) return 0.5 - 0.5 * Math.cos(Math.PI * (h - 6) / 9);
  const t = ((h - 15 + 24) % 24) / 15;
  return 0.5 + 0.5 * Math.cos(Math.PI * t);
}

// clima: {tmax[12], tmin[12], rh[12], td[12]|null}
function buildYear(clima, sd, seed) {
  const rnd = mulberry32(seed);
  const hours = [];
  let anom = 0;
  for (let m = 0; m < 12; m++) {
    const tmean = (clima.tmax[m] + clima.tmin[m]) / 2;
    const tdM = clima.td && clima.td[m] != null ? clima.td[m] : dewFromRH(tmean, clima.rh[m]);
    for (let d = 0; d < DAYS[m]; d++) {
      anom = 0.7 * anom + Math.sqrt(1 - 0.49) * gauss(rnd) * sd; // persistenza tipo ondata di calore
      const tx = clima.tmax[m] + anom, tn = clima.tmin[m] + anom;
      const td = tdM + 0.5 * anom;
      for (let h = 0; h < 24; h++) {
        const T = tn + (tx - tn) * diurnal(h);
        const Tdh = Math.min(td, T - 0.1);
        const RH = rhFromDew(T, Tdh);
        hours.push({ m, T, RH, Twb: Math.min(T, wetBulb(T, RH)) });
      }
    }
  }
  return hours;
}

function clamp(x, a, b) { return Math.max(a, Math.min(b, x)); }

// p: parametri del progetto
function simulate(p, climaHours) {
  const itKW = p.itMW * 1000 * p.load;
  const mon = Array.from({ length: 12 }, () => ({ it: 0, tot: 0, water: 0, hoursWater: 0 }));
  let itE = 0, totE = 0, water = 0, evapTot = 0, hoursWater = 0, hoursOut = 0, heat = 0, mechHours = 0, pueHourMax = 0;
  let waterHourMax = 0; // solo uscita aggiuntiva: litri nell'ora di massimo prelievo (nessun effetto sui calcoli)
  for (const hr of climaHours) {
    const { T, Twb } = hr;
    const Q = itKW * p.kHeat; // calore da smaltire (kW)
    let cool = 0, evap = 0, makeup = 0;
    if (p.sys === 'dry') {
      // chiller ad aria con free cooling, circuito chiuso, opzionale pre-raffreddamento adiabatico
      let Teff = T, dPre = 0;
      if (p.adiabatic && T > p.tSwitch) { dPre = p.eps * (T - Twb); Teff = T - dPre; }
      const fMech = clamp((Teff - p.tFcFull) / (p.tFcNone - p.tFcFull), 0, 1);
      const cop = clamp(p.copA - p.copB * Teff, 2.2, 9);
      const W = fMech * Q / cop;
      cool = p.fan * Q + W;
      if (fMech > 0) mechHours += 1;
      if (dPre > 0) { evap = (Q + W) * L_PER_KWH_HEAT * dPre / p.dTcoil; }
    } else if (p.sys === 'tower') {
      // torri evaporative + chiller raffreddati ad acqua, economizzatore lato acqua
      const fMech = clamp((Twb - p.tFcFull) / (p.tFcNone - p.tFcFull), 0, 1);
      const cop = clamp(p.copA - p.copB * Twb, 3.5, 11);
      const W = fMech * Q / cop;
      cool = p.fan * Q + W;
      if (fMech > 0) mechHours += 1;
      const dryMode = T < p.tDry; // torri ibride: a secco quando fa freddo
      if (!dryMode) evap = (Q + W) * L_PER_KWH_HEAT * p.fEvap;
    } else if (p.sys === 'direct') {
      // aria esterna diretta + raffreddamento evaporativo sopra soglia, senza chiller
      cool = p.fan * Q;
      if (T > p.tSwitch) {
        const need = T - p.tSup;
        const can = p.eps * (T - Twb);
        const dPre = Math.max(0, Math.min(need, can));
        if (can < need) hoursOut += 1;
        evap = Q * L_PER_KWH_HEAT * dPre / p.dTair;
      }
    }
    if (evap > 0) { makeup = evap * p.coc / (p.coc - 1); hoursWater += 1; }
    const acc = itKW * p.accessori; // usi accessori (umidificazione, servizi) L/h
    const totKW = itKW + itKW * p.losses + cool;
    if (totKW / itKW > pueHourMax) pueHourMax = totKW / itKW;
    itE += itKW; totE += totKW; water += makeup + acc; evapTot += evap; heat += Q;
    if (makeup + acc > waterHourMax) waterHourMax = makeup + acc;
    const mm = mon[hr.m]; mm.it += itKW; mm.tot += totKW; mm.water += makeup + acc; if (evap > 0) mm.hoursWater += 1;
  }
  return {
    itMWh: itE / 1000, totMWh: totE / 1000, pue: totE / itE, waterPeakM3h: waterHourMax / 1000,
    waterM3: water / 1000, wue: water / itE, evapM3: evapTot / 1000,
    hoursWater, hoursOut, mechHours, heatMWh: heat / 1000, pueHourMax,
    months: mon.map(x => ({ pue: x.tot / x.it, waterM3: x.water / 1000, hoursWater: x.hoursWater, itMWh: x.it / 1000 })),
  };
}

// Più anni sintetici (stesso clima medio, giornate diverse) per avere media e forbice
const _yearCache = {};
function getYears(clima, sd, n) {
  const key = JSON.stringify(clima) + '|' + sd + '|' + n;
  if (!_yearCache[key]) {
    const ys = [];
    for (let i = 0; i < n; i++) ys.push(buildYear(clima, sd, 1000 + i * 7919));
    _yearCache[key] = ys;
  }
  return _yearCache[key];
}
function simulateMulti(p, clima, sd, n) {
  return simulateMultiHours(p, getYears(clima, sd, n));
}
// Stessa aggregazione di simulateMulti, ma su anni orari forniti dall'esterno
// (es. un anno meteorologico tipo PVGIS: years = [ore]). Con un solo anno la forbice è nulla.
function simulateMultiHours(p, years) {
  const runs = years.map(H => simulate(p, H));
  const avg = k => runs.reduce((s, r) => s + r[k], 0) / runs.length;
  const min = k => Math.min(...runs.map(r => r[k]));
  const max = k => Math.max(...runs.map(r => r[k]));
  const out = {};
  for (const k of ['itMWh', 'totMWh', 'waterM3', 'evapM3', 'hoursWater', 'hoursOut', 'mechHours', 'heatMWh']) out[k] = avg(k);
  out.pue = out.totMWh / out.itMWh;
  out.wue = out.waterM3 * 1000 / (out.itMWh * 1000);
  out.waterMin = min('waterM3'); out.waterMax = max('waterM3');
  out.pueMin = min('pue'); out.pueMax = max('pue'); out.pueHourMax = max('pueHourMax');
  out.waterPeakM3h = max('waterPeakM3h'); // prelievo massimo orario nell'anno peggiore
  out.months = Array.from({ length: 12 }, (_, m) => {
    const it = runs.reduce((s, r) => s + r.months[m].itMWh, 0);
    const pueW = runs.reduce((s, r) => s + r.months[m].pue * r.months[m].itMWh, 0) / it;
    return { pue: pueW, waterM3: runs.reduce((s, r) => s + r.months[m].waterM3, 0) / runs.length };
  });
  return out;
}
function hoursAbove(clima, sd, n, T) {
  return hoursAboveHours(getYears(clima, sd, n), T);
}
function hoursAboveHours(years, T) {
  return years.reduce((s, H) => s + H.filter(h => h.T > T).length, 0) / years.length;
}

// Converte le ore dell'anno meteorologico tipo PVGIS (campi 'time(UTC)' AAAAMMGG:hhmm, T2m °C, RH %)
// nel formato usato da simulate(): {m, T, RH, Twb}. Bulbo umido con la stessa formula di buildYear.
function hoursFromPVGIS(tmyHourly) {
  return tmyHourly.map(h => {
    const T = h.T2m;
    const RH = clamp(h.RH, 1, 100);
    const m = parseInt(String(h['time(UTC)']).slice(4, 6), 10) - 1;
    return { m, T, RH, Twb: Math.min(T, wetBulb(T, RH)) };
  });
}

// Anni reali da PVGIS: temperature orarie vere (serie 2005–2023, senza umidità) e, per l'umidità,
// il punto di rugiada medio per mese e ora del giorno ricavato dall'anno tipo (TMY) dello stesso punto.
// Stesso criterio di buildYear: rugiada mensile tipica, limitata a T − 0,1 °C.
// tmyHourly: ore TMY {'time(UTC)', T2m, RH}; anni: {anno: [8760 temperature °C, dall'1/1 ore 0 UTC]}
function yearsFromPVGIS(tmyHourly, anni) {
  const sum = Array.from({ length: 12 }, () => new Array(24).fill(0));
  const cnt = Array.from({ length: 12 }, () => new Array(24).fill(0));
  for (const h of tmyHourly) {
    const t = String(h['time(UTC)']);
    const m = parseInt(t.slice(4, 6), 10) - 1, hr = parseInt(t.slice(9, 11), 10);
    sum[m][hr] += dewFromRH(h.T2m, clamp(h.RH, 1, 100)); cnt[m][hr] += 1;
  }
  const meseOra = [];
  DAYS.forEach((d, m) => { for (let i = 0; i < d * 24; i++) meseOra.push(m); });
  return Object.keys(anni).sort().map(y => anni[y].map((T, i) => {
    const m = meseOra[i], hr = i % 24;
    const Td = Math.min(sum[m][hr] / cnt[m][hr], T - 0.1);
    const RH = rhFromDew(T, Td);
    return { m, T, RH, Twb: Math.min(T, wetBulb(T, RH)) };
  }));
}

function gridFactor(mix, f, includeHydroEvap) {
  // mix in GWh; f in L/kWh
  let tot = 0, w = 0;
  const parts = [];
  for (const k of Object.keys(mix)) {
    tot += mix[k];
  }
  for (const k of Object.keys(mix)) {
    let fk = f[k] || 0;
    if (k === 'idro' && includeHydroEvap) fk = f.idroEvap;
    const c = mix[k] / tot * fk;
    w += c; parts.push({ k, share: mix[k] / tot, f: fk, c });
  }
  return { factor: w, parts };
}

function classPUE(x) { return x <= 1.15 ? 'A' : x <= 1.25 ? 'B' : x <= 1.35 ? 'C' : x <= 1.5 ? 'D' : x <= 1.7 ? 'E' : x <= 1.9 ? 'F' : 'G'; }
function classWUE(x) { return x <= 0.1 ? 'A' : x <= 0.2 ? 'B' : x <= 0.4 ? 'C' : x <= 0.6 ? 'D' : x <= 0.8 ? 'E' : x <= 1.0 ? 'F' : 'G'; }

if (typeof module !== 'undefined') module.exports = { buildYear, simulate, simulateMulti, simulateMultiHours, hoursAbove, hoursAboveHours, hoursFromPVGIS, yearsFromPVGIS, gridFactor, classPUE, classWUE, L_PER_KWH_HEAT };
