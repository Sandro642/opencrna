"""Régénère data/geo.json à partir des sources ouvertes.
Usage : python3 data/gen_geo.py   (télécharge les fichiers dans data/raw/)
Sources : OurAirports (navaids.csv), VATSpy Data Project (Boundaries.geojson, VATSpy.dat)."""
import json, csv, os, urllib.request
D=os.path.dirname(os.path.abspath(__file__)); RAW=os.path.join(D,'raw'); os.makedirs(RAW,exist_ok=True)
SRC={'navaids.csv':'https://raw.githubusercontent.com/davidmegginson/ourairports-data/main/navaids.csv',
     'b.json':'https://raw.githubusercontent.com/vatsimnetwork/vatspy-data-project/master/Boundaries.geojson',
     'vatspy.dat':'https://raw.githubusercontent.com/vatsimnetwork/vatspy-data-project/master/VATSpy.dat'}
for f,u in SRC.items():
  p=os.path.join(RAW,f)
  if not os.path.exists(p): urllib.request.urlretrieve(u,p)
d=json.load(open(os.path.join(RAW,'b.json')))
F={f['properties']['id']:f for f in d['features']}
out={'sectors':{},'firs':{}}
r=lambda c:[[round(p[1],4),round(p[0],4)] for p in c]
for k in F:
  if k.startswith('LFBB-'): out['sectors'][k[5:]]=r(F[k]['geometry']['coordinates'][0][0])
out['lfbb']=r(F['LFBB']['geometry']['coordinates'][0][0])
for k in ('LFRR','LFFF','LFMM','LECM','LECB','LFEE'):
  if k in F: out['firs'][k]=[r(P[0]) for P in F[k]['geometry']['coordinates']]
seen={}
for row in csv.DictReader(open(os.path.join(RAW,'navaids.csv'),encoding='utf-8')):
  try: la=float(row['latitude_deg']); lo=float(row['longitude_deg'])
  except: continue
  if 41.0<la<49.2 and -4.6<lo<4.8 and row['type'] in ('VOR','VOR-DME','VORTAC') and row['iso_country'] in ('FR','ES','AD'):
    seen.setdefault(row['ident'],[row['ident'],row['name'],round(la,4),round(lo,4),int(row['frequency_khz'])/1000])
out['vors']=list(seen.values())
aps={}
for line in open(os.path.join(RAW,'vatspy.dat'),encoding='utf-8',errors='ignore'):
  p=line.strip().split('|')
  if len(p)>=6 and len(p[0])==4 and p[0][:2] in ('LF','LE','LP','EG','LS'):
    try: aps[p[0]]=[p[1],round(float(p[2]),4),round(float(p[3]),4)]
    except: pass
want=['LFBD','LFBO','LFBZ','LFBP','LFBT','LFBH','LFBE','LFBA','LFBL','LFBI','LFBG','LFBU','LFBV','LFBX','LFCR','LFBM','LFBC','LFBY','LFCK','LFMK','LFRS','LFRN','LFPO','LFPG','LFLC','LFLL','LFML','LFMN','LFMT','LFMP','LEBB','LESO','LEVT','LEPP','LELL','LEBL','LEMD','LEZG','LEGE','LEDA','LEXJ','LEST','LELO','LFOT','LFLX','LFMD','LFKJ']
out['airports']={k:aps[k] for k in want if k in aps}
json.dump(out,open(os.path.join(D,'geo.json'),'w'),separators=(',',':'))
print('geo.json écrit :',len(out['vors']),'VOR,',len(out['airports']),'terrains,',len(out['sectors']),'secteurs')
