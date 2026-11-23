"""Geometria semplice per distanze tra il lotto e oggetti vicini (vincoli, aree protette, linee elettriche).

Coordinate in ingresso: GeoJSON (lon, lat). Calcolo su piano locale in metri centrato sul lotto
(raggi dell'ellissoide WGS84): errore trascurabile entro qualche decina di km.
"""
import math

A, E2 = 6378137.0, 6.69437999014e-3


class PianoLocale:
    def __init__(self, lat0: float, lon0: float):
        s = math.sin(math.radians(lat0))
        n = A / math.sqrt(1 - E2 * s * s)
        m = A * (1 - E2) / (1 - E2 * s * s) ** 1.5
        self.lat0, self.lon0 = lat0, lon0
        self.kx = math.radians(1) * n * math.cos(math.radians(lat0))
        self.ky = math.radians(1) * m

    def xy(self, lon: float, lat: float, *_quota) -> tuple:
        return ((lon - self.lon0) * self.kx, (lat - self.lat0) * self.ky)

    def lonlat(self, x: float, y: float) -> tuple:
        return (self.lon0 + x / self.kx, self.lat0 + y / self.ky)


def parti(geom: dict) -> tuple:
    """Scompone una geometria GeoJSON in (anelli di poligoni [lista di poligoni, ciascuno lista di anelli], linee, punti)."""
    t, c = geom["type"], geom["coordinates"]
    if t == "Polygon":
        return [c], [], []
    if t == "MultiPolygon":
        return list(c), [], []
    if t == "LineString":
        return [], [c], []
    if t == "MultiLineString":
        return [], list(c), []
    if t == "Point":
        return [], [], [c]
    if t == "MultiPoint":
        return [], [], list(c)
    raise ValueError(f"geometria non gestita: {t}")


def _seg_dist(p, a, b) -> float:
    (px, py), (ax, ay), (bx, by) = p, a, b
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def _incrocia(a, b, c, d) -> bool:
    def o(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    return (o(a, b, c) > 0) != (o(a, b, d) > 0) and (o(c, d, a) > 0) != (o(c, d, b) > 0)


def _in_anello(p, r) -> bool:
    x, y, c = p[0], p[1], False
    for i in range(len(r) - 1):
        (x1, y1), (x2, y2) = r[i], r[i + 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def _in_poligono(p, poly) -> bool:
    return _in_anello(p, poly[0]) and not any(_in_anello(p, h) for h in poly[1:])


class Lotto:
    """Il lotto (una o più particelle) proiettato sul piano locale."""

    def __init__(self, geometrie: list):
        tutti = [pt[:2] for g in geometrie for poly in parti(g)[0] for pt in poly[0]]
        lon0 = sum(p[0] for p in tutti) / len(tutti)
        lat0 = sum(p[1] for p in tutti) / len(tutti)
        self.piano = PianoLocale(lat0, lon0)
        self.poligoni = [[[self.piano.xy(*pt) for pt in ring] for ring in poly]
                         for g in geometrie for poly in parti(g)[0]]
        self.segmenti = [(r[i], r[i + 1]) for poly in self.poligoni for r in poly for i in range(len(r) - 1)]
        xs = [p[0] for s in self.segmenti for p in s]
        ys = [p[1] for s in self.segmenti for p in s]
        self.box = (min(xs), min(ys), max(xs), max(ys))
        cx, cy = (self.box[0] + self.box[2]) / 2, (self.box[1] + self.box[3]) / 2
        self.centro = self.piano.lonlat(cx, cy)  # (lon, lat)
        self.raggio = max(math.hypot(x - cx, y - cy) for x, y in zip(xs, ys))  # cerchio che contiene il lotto

    def riquadro(self, margine_m: float) -> tuple:
        """(sud, ovest, nord, est) in gradi, allargato del margine."""
        o, s = self.piano.lonlat(self.box[0] - margine_m, self.box[1] - margine_m)
        e, n = self.piano.lonlat(self.box[2] + margine_m, self.box[3] + margine_m)
        return s, o, n, e

    def contiene(self, p) -> bool:
        return any(_in_poligono(p, poly) for poly in self.poligoni)

    def distanza(self, geom: dict, max_m: float = 1e9) -> float:
        """Distanza minima in metri tra il lotto e la geometria (0 se si toccano o si sovrappongono)."""
        polys, linee, punti = parti(geom)
        P = self.piano
        bx0, by0, bx1, by1 = self.box[0] - max_m, self.box[1] - max_m, self.box[2] + max_m, self.box[3] + max_m
        best = math.inf
        pp = [[[P.xy(*pt) for pt in ring] for ring in poly] for poly in polys]
        # 1) il lotto è dentro un poligono dell'oggetto?
        cx, cy = (self.box[0] + self.box[2]) / 2, (self.box[1] + self.box[3]) / 2
        if any(_in_poligono((cx, cy), poly) for poly in pp):
            return 0.0
        segs = [(r[i], r[i + 1]) for poly in pp for r in poly for i in range(len(r) - 1)]
        for ln in linee:
            q = [P.xy(*pt) for pt in ln]
            segs += [(q[i], q[i + 1]) for i in range(len(q) - 1)]
        for a, b in segs:
            if max(a[0], b[0]) < bx0 or min(a[0], b[0]) > bx1 or max(a[1], b[1]) < by0 or min(a[1], b[1]) > by1:
                continue  # segmento lontano: non può essere il più vicino entro max_m
            if self.contiene(a):
                return 0.0
            for c, d in self.segmenti:
                if _incrocia(a, b, c, d):
                    return 0.0
                best = min(best, _seg_dist(a, c, d), _seg_dist(b, c, d), _seg_dist(c, a, b), _seg_dist(d, a, b))
        for pt in punti:
            q = P.xy(*pt)
            if self.contiene(q):
                return 0.0
            best = min(best, min(_seg_dist(q, c, d) for c, d in self.segmenti))
        return best
