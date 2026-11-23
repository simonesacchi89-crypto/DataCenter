// Versione dimostrativa: le richieste al programma locale sono servite dai dati registrati in DEMO.
(function () {
  const fetchVero = window.fetch.bind(window);
  const risposta = (obj, status = 200) => Promise.resolve(new Response(JSON.stringify(obj), { status, headers: { 'Content-Type': 'application/json' } }));
  const errore = (status, detail) => risposta({ detail }, status);
  const SOLO_MAGENTA = 'Versione dimostrativa: sono registrati solo i dati di Magenta (ex Novaceta). Per altri siti serve la versione completa.';
  const norm = t => String(t || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim();
  const dist = (la1, lo1, la2, lo2) => Math.hypot((la1 - la2) * 111150, (lo1 - lo2) * 111320 * Math.cos(la1 * Math.PI / 180));
  const vicinoLotto = (lat, lon, m = 1500) => dist(lat, lon, 45.4676, 8.8732) <= m;

  function anelli(g) { return (g.type === 'Polygon' ? [g.coordinates] : g.coordinates); }
  function bbox(g) { const pts = anelli(g).flatMap(p => p[0]); return [Math.min(...pts.map(q => q[1])), Math.min(...pts.map(q => q[0])), Math.max(...pts.map(q => q[1])), Math.max(...pts.map(q => q[0]))]; }
  function dentroAnello(x, y, r) { let c = false; for (let i = 0; i < r.length - 1; i++) { const [x1, y1] = r[i], [x2, y2] = r[i + 1]; if ((y1 > y) !== (y2 > y) && x < (x2 - x1) * (y - y1) / (y2 - y1) + x1) c = !c; } return c; }
  function dentro(lon, lat, g) { return anelli(g).some(p => dentroAnello(lon, lat, p[0]) && !p.slice(1).some(h => dentroAnello(lon, lat, h))); }
  DEMO.particelle.forEach(p => { p._bbox = bbox(p.geometry); });
  const conMeta = extra => Object.assign({}, DEMO.meta_catasto, extra);
  const pulita = p => { const q = Object.assign({}, p); delete q._bbox; return q; };

  function api(url, init) {
    const u = new URL(url, 'http://demo.local');
    const q = k => u.searchParams.get(k);
    switch (u.pathname) {
      case '/api/particelle/cerca': {
        if (norm(q('comune')) !== 'magenta') return errore(404, SOLO_MAGENTA);
        if (+q('foglio') !== 4) return errore(404, 'Versione dimostrativa: per Magenta è registrato solo il foglio 4.');
        const cercate = q('particelle').split(/[,;]/).map(s => s.trim().toUpperCase()).filter(Boolean);
        const trovate = DEMO.particelle.filter(p => p.foglio === 4 && cercate.includes(String(p.particella).toUpperCase()));
        return risposta(conMeta({ comune: DEMO.comune, fogli: ['E801_000400'], particelle: trovate.map(pulita),
          non_trovate: cercate.filter(c => !trovate.some(p => String(p.particella).toUpperCase() === c)) }));
      }
      case '/api/particella/punto': {
        const lat = +q('lat'), lon = +q('lon');
        const p = DEMO.particelle.find(x => lat >= x._bbox[0] && lat <= x._bbox[2] && lon >= x._bbox[1] && lon <= x._bbox[3] && dentro(lon, lat, x.geometry));
        return p ? risposta(conMeta({ particelle: [pulita(p)] })) : errore(404, 'Versione dimostrativa: nessuna particella registrata in questo punto (sono registrate quelle intorno all\'ex Novaceta).');
      }
      case '/api/particelle/riquadro': {
        const s = +q('s'), w = +q('w'), n = +q('n'), e = +q('e');
        return risposta(conMeta({ particelle: DEMO.particelle.filter(p => !(p._bbox[2] < s || p._bbox[0] > n || p._bbox[3] < w || p._bbox[1] > e)).map(pulita) }));
      }
      case '/api/clima': {
        const lat = +q('lat'), lon = +q('lon');
        const k = Object.keys(DEMO.clima).find(k => { const [a, b] = k.split('_').map(Number); return dist(lat, lon, a, b) < 5000; });
        return k ? risposta(DEMO.clima[k]) : errore(502, 'Versione dimostrativa: il clima reale è registrato solo per Magenta e Rho-Pero.');
      }
      case '/api/controlli': {
        let body = {}; try { body = JSON.parse(init && init.body || '{}'); } catch (e) { /* vuoto */ }
        const g = (body.geometrie || [])[0];
        const r0 = g ? anelli(g)[0][0] : null;
        const c = r0 ? r0.reduce((a, x) => [a[0] + x[0] / r0.length, a[1] + x[1] / r0.length], [0, 0]) : null;
        if (!c || !vicinoLotto(c[1], c[0])) return errore(502, SOLO_MAGENTA);
        return risposta(DEMO.controlli);
      }
      case '/api/ortofoto': {
        const s = +q('s'), w = +q('w'), n = +q('n'), e = +q('e');
        const rec = DEMO.ortofoto[q('anno') || '2012'];
        return rec && vicinoLotto((s + n) / 2, (w + e) / 2) ? risposta(rec) : errore(502, 'Versione dimostrativa: foto aeree registrate solo per l\'ex Novaceta.');
      }
    }
    if (u.pathname === '/esempi/foto_demo/foto.json') return risposta(DEMO.foto_meta);
    const m = u.pathname.match(/^\/esempi\/foto_demo\/(.+\.jpg)$/);
    if (m && DEMO.foto_file[m[1]]) {
      const bin = atob(DEMO.foto_file[m[1]]), arr = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
      return Promise.resolve(new Response(new Blob([arr], { type: 'image/jpeg' })));
    }
    return null;
  }

  window.fetch = function (url, init) {
    const s = String(url);
    if (s.startsWith('/api/') || s.startsWith('/esempi/')) return api(s, init) || errore(404, 'Non disponibile nella versione dimostrativa');
    return fetchVero(url, init);
  };
})();
