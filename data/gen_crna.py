"""Ajoute à data/geo.json les autres CRNA français (clé crna), les FIR étrangères voisines, et élargit VOR et terrains à toute la France.
Usage : python3 data/gen_crna.py   (après gen_geo.py ; nécessite shapely : pip install shapely)
Sources : VATSpy Data Project (Boundaries.geojson, VATSpy.dat), OurAirports (navaids.csv), dans data/raw/.
Les limites VATSpy des CRNA se recouvrent (la FIR LFFF contient LFEE, déborde sur LFRR et LFBB) : on en tire des aires
disjointes (Reims = partie de la FIR Paris à l'est d'une ligne 3,6-4,4°E). Le découpage en secteurs des CRNA autres que LFBB
est FICTIF : cellules de Voronoï autour de centres choisis (k-moyennes), deux couches (inférieure FL115-345, supérieure
FL345-660). Noms de secteurs et fréquences FICTIFS."""
import json, csv, os, urllib.request
from shapely.geometry import shape, Polygon, MultiPoint, Point
from shapely.ops import voronoi_diagram
D = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(D, 'raw'); os.makedirs(RAW, exist_ok=True)
SRC = {'navaids.csv': 'https://raw.githubusercontent.com/davidmegginson/ourairports-data/main/navaids.csv',
       'b.json': 'https://raw.githubusercontent.com/vatsimnetwork/vatspy-data-project/master/Boundaries.geojson',
       'vatspy.dat': 'https://raw.githubusercontent.com/vatsimnetwork/vatspy-data-project/master/VATSpy.dat'}
for f, u in SRC.items():
    p = os.path.join(RAW, f)
    if not os.path.exists(p): urllib.request.urlretrieve(u, p)
geo = json.load(open(os.path.join(D, 'geo.json')))
F = {f['properties']['id']: f for f in json.load(open(os.path.join(RAW, 'b.json')))['features']}
G = {c: shape(F[c]['geometry']).buffer(0) for c in F if c in ('LFBB', 'LFFF', 'LFRR', 'LFMM', 'LFEE')}

def clean(g):
    g = g.buffer(0.02).buffer(-0.02)
    return max(g.geoms, key=lambda p: p.area) if g.geom_type == 'MultiPolygon' else g
def ring(g, tol=0.015):
    g = g.simplify(tol)
    if g.geom_type == 'MultiPolygon': g = max(g.geoms, key=lambda p: p.area)
    return [[round(y, 4), round(x, 4)] for x, y in list(g.exterior.coords)[:-1]]

# aires disjointes des CRNA
EAST = [(51.6, 4.3), (50.1, 4.2), (49.4, 3.6), (48.6, 3.6), (47.8, 4.1), (47.0, 4.3), (45.9, 4.4)]
E = Polygon([(lo, la) for la, lo in EAST] + [(10, 45.9), (10, 51.6)])
U = G['LFFF'].difference(G['LFBB']).difference(G['LFMM'])
A = {'LFBB': G['LFBB'], 'LFMM': clean(G['LFMM']), 'LFEE': clean(U.intersection(E)), 'LFFF': clean(U.difference(E))}
A['LFRR'] = clean(G['LFRR'].difference(A['LFFF']).difference(G['LFBB']))

# secteurs FICTIFS : code, nom, centre (lat, lon), fréquence
SECS = {
 'LFFF': {'lo': [('NO', 'Flandres / Artois', 50.53, 2.39, '128.380'), ('PI', 'Picardie / Valois', 49.65, 2.94, '126.105'),
                 ('NM', 'Normandie / Vexin', 49.63, 0.78, '125.830'), ('PE', 'Perche / Beauce', 48.60, 0.85, '127.205'),
                 ('BR', 'Brie / Gâtinais', 48.44, 2.88, '132.830'), ('TO', 'Touraine / Sologne', 47.58, 0.55, '124.455'),
                 ('NV', 'Nivernais / Morvan', 47.15, 3.73, '133.380')],
          'up': [('UN', 'Supérieur Nord', 49.84, 2.24, '135.305'), ('UO', 'Supérieur Ouest', 48.24, 0.73, '134.155'),
                 ('US', 'Supérieur Sud', 47.67, 3.44, '131.155')]},
 'LFEE': {'lo': [('CH', 'Champagne / Ardennes', 49.33, 4.61, '125.555'), ('LO', 'Lorraine / Alsace', 48.80, 6.79, '127.430'),
                 ('AU', 'Aube / Haute-Marne', 48.25, 4.80, '126.730'), ('FC', 'Franche-Comté / Vosges', 47.76, 6.57, '128.705'),
                 ('BO', 'Bourgogne', 47.02, 5.03, '124.355')],
          'up': [('UN', 'Supérieur Nord', 48.91, 5.46, '133.055'), ('US', 'Supérieur Sud', 47.48, 5.64, '134.405')]},
 'LFRR': {'lo': [('CO', 'Cotentin / Bocage', 48.98, -1.57, '126.880'), ('BN', 'Bretagne Nord', 48.64, -4.13, '125.280'),
                 ('MO', 'Manche Ouest', 48.31, -6.76, '127.930'), ('PL', 'Pays de la Loire', 47.00, -1.82, '124.680'),
                 ('BS', 'Bretagne Sud / Iroise', 46.75, -4.62, '128.180'), ('OC', 'Océan', 45.86, -6.68, '129.880'),
                 ('GG', 'Golfe de Gascogne', 45.02, -3.26, '123.980')],
          'up': [('UE', 'Supérieur Est', 48.50, -2.15, '132.305'), ('UN', 'Supérieur Nord', 48.38, -6.08, '135.580'),
                 ('UO', 'Supérieur Ouest', 46.00, -6.27, '133.705'), ('US', 'Supérieur Sud', 45.60, -2.88, '134.705')]},
 'LFMM': {'lo': [('LY', 'Lyonnais / Rhône', 45.54, 4.85, '127.805'), ('AL', 'Alpes du Sud / Provence', 44.32, 5.70, '125.930'),
                 ('AZ', 'Côte d\'Azur', 43.15, 7.11, '128.055'), ('GL', 'Golfe du Lion', 42.86, 4.70, '126.505'),
                 ('CO', 'Corse', 42.18, 8.62, '124.580'), ('ME', 'Méditerranée', 41.35, 6.04, '129.580'),
                 ('MS', 'Méditerranée Sud', 39.81, 6.41, '123.630')],
          'up': [('UN', 'Supérieur Nord', 44.20, 5.14, '133.555'), ('UE', 'Supérieur Est', 42.44, 7.77, '135.830'),
                 ('US', 'Supérieur Sud', 40.27, 6.14, '132.155')]},
}
def voronoi(area, seeds):
    pts = MultiPoint([(lo, la) for _, _, la, lo, _ in seeds])
    cells = voronoi_diagram(pts, envelope=area.envelope.buffer(3))
    out = {}
    for code, name, la, lo, fq in seeds:
        c = next(c for c in cells.geoms if c.contains(Point(lo, la)))
        out[code] = clean(c.intersection(area))
    return out
crna = {}
for c, a in A.items():
    d = {'area': ring(a), 'sec': {}}
    if c == 'LFBB':
        names = {'R': 'Poitou-Charentes', 'Z': 'Landes / Côte basque', 'N': 'Pyrénées', 'X': 'Quercy / Agenais', 'H': 'Haut-Languedoc / Roussillon',
                 'L': 'Limousin', 'T': 'Auvergne', 'P': 'Berry', 'UN': 'Supérieur Nord', 'US': 'Supérieur Sud'}
        fq = {'H': '123.855', 'L': '126.255', 'N': '125.105', 'P': '128.455', 'R': '133.505', 'T': '127.680', 'X': '129.355', 'Z': '124.505', 'UN': '132.555', 'US': '134.880'}
        for k, p in geo['sectors'].items(): d['sec'][k] = {'n': names[k], 'f': fq[k], 'u': int(k in ('UN', 'US')), 'p': p}
    else:
        for lay in ('lo', 'up'):
            cells = voronoi(a, SECS[c][lay])
            for code, name, la, lo, f in SECS[c][lay]: d['sec'][code] = {'n': name, 'f': f, 'u': int(lay == 'up'), 'p': ring(cells[code])}
    crna[c] = d
geo['crna'] = crna
fq = [s['f'] for c in crna.values() for s in c['sec'].values()]
assert len(fq) == len(set(fq)), 'fréquences en double'

# FIR voisines : aires CRNA pour la France, VATSpy pour l'étranger
firs = {c: [ring(A[c], .02)] for c in A}
for k in ('EGTT', 'EGGX', 'EBBU', 'EDGG', 'EDMM', 'LSAS', 'LIMM', 'LIRR', 'LECM', 'LECB', 'LPPC'):
    g = shape(F[k]['geometry']).buffer(0)
    firs[k] = [ring(p, .02) for p in (g.geoms if g.geom_type == 'MultiPolygon' else [g]) if p.area > .05]
geo['firs'] = firs

# VOR : France et pays voisins (on garde ceux de LFBB en premier : même identifiant = même balise)
vors = {v[0]: v for v in geo['vors']}
for row in csv.DictReader(open(os.path.join(RAW, 'navaids.csv'), encoding='utf-8')):
    try: la = float(row['latitude_deg']); lo = float(row['longitude_deg'])
    except ValueError: continue
    if row['type'] in ('VOR', 'VOR-DME', 'VORTAC') and row['iso_country'] in ('FR', 'ES', 'AD', 'GB', 'GG', 'JE', 'BE', 'LU', 'DE', 'CH', 'IT') \
       and 40.5 < la < 52.6 and -6.5 < lo < 10.6 and not (row['iso_country'] == 'GB' and row['ident'] == 'BCN'):
        vors.setdefault(row['ident'], [row['ident'], row['name'], round(la, 4), round(lo, 4), int(row['frequency_khz']) / 1000])
geo['vors'] = list(vors.values())
aps = {}
for line in open(os.path.join(RAW, 'vatspy.dat'), encoding='utf-8', errors='ignore'):
    p = line.strip().split('|')
    if len(p) >= 6 and len(p[0]) == 4:
        try: aps[p[0]] = [p[1], round(float(p[2]), 4), round(float(p[3]), 4)]
        except ValueError: pass
want = ['LFPG', 'LFPO', 'LFPB', 'LFQQ', 'LFOB', 'LFOK', 'LFRS', 'LFRN', 'LFRB', 'LFRK', 'LFRG', 'LFRD', 'LFRH', 'LFRQ', 'LFRZ', 'LFOT', 'LFML', 'LFMN',
        'LFLL', 'LFMT', 'LFTH', 'LFKJ', 'LFKB', 'LFKF', 'LFKC', 'LFLS', 'LFLB', 'LFLP', 'LFMP', 'LFMV', 'LFTW', 'LFST', 'LFSB', 'LFJL', 'LFSD', 'LFLC',
        'LSGG', 'LSZH', 'LIMC', 'LIML', 'LIRF', 'LIEO', 'LIEE', 'LEPA', 'LEIB', 'LEBL', 'LEMD', 'LPPT', 'EBBR', 'EHAM', 'EDDF', 'EDDM', 'EGLL',
        'DAAG', 'DTTA', 'DAON', 'GMMN', 'KJFK', 'KBOS', 'CYUL', 'KIAD', 'KATL', 'KORD', 'GOBD', 'GOOY']
for k in want:
    if k in aps: geo['airports'].setdefault(k, aps[k])
json.dump(geo, open(os.path.join(D, 'geo.json'), 'w'), separators=(',', ':'))
print('geo.json : CRNA', {c: len(d['sec']) for c, d in crna.items()}, '·', len(firs), 'FIR ·', len(geo['vors']), 'VOR ·', len(geo['airports']), 'terrains')
