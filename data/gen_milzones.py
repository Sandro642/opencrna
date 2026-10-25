"""Ajoute à data/geo.json (clé "milz") les zones militaires réglementées/dangereuses utiles au poste Essais en vol.
Source : eAIP France ENR 5.1 (zones R/D) et ENR 5.2 (TRA d'entraînement) (SIA, https://www.sia.aviation-civile.gouv.fr), édition passée en argument.
Usage : python3 data/gen_milzones.py eAIP_01_OCT_2026/FRANCE/AIRAC-2026-10-01
Limites latérales et verticales officielles ; les segments « limite des eaux territoriales » et les arcs
sont remplacés par des segments droits (signalé par approx=true)."""
import re, sys, os, json, html, math, urllib.request
D=os.path.dirname(os.path.abspath(__file__)); RAW=os.path.join(D,'raw'); os.makedirs(RAW,exist_ok=True)
ED=sys.argv[1] if len(sys.argv)>1 else 'eAIP_01_OCT_2026/FRANCE/AIRAC-2026-10-01'
def page(n):
  p=os.path.join(RAW,'enr5%d.html'%n)
  if not os.path.exists(p): urllib.request.urlretrieve('https://www.sia.aviation-civile.gouv.fr/media/dvd/'+ED+'/html/eAIP/FR-ENR-5.%d-fr-FR.html'%n,p)
  return html.unescape(re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',open(p,encoding='utf-8',errors='replace').read())))
t=page(1)+' '+page(2)
# Zones retenues (nom ENR 5.1 -> identifiant court utilisé en jeu)
SEL={'D 31 D CAZAUX':'D31D','D 32':'D32','D 33':'D33','D 300 A ZENA GASCOGNE':'D300A','R 31 H CAZAUX':'R31H','R 31 B CAZAUX':'R31B',
     'R 31 A5 CAZAUX':'R31A5','R 34 A2 MONT DE MARSAN':'R34A2','R 61 H BORDEAUX':'R61H','R 49 H1 COGNAC':'R49H1','R 49 H2 COGNAC':'R49H2',
     'R 170 B CALAMAR':'R170B','R 68 C':'R68C',
     # TRA d'entraînement au combat (ENR 5.2) : secteur Mont-de-Marsan (34), Massif central (43), Poitou (10)
     'TRA 34 A':'TRA34A','TRA 34 B':'TRA34B','TRA 34 C':'TRA34C','TRA 34 D':'TRA34D','TRA 34 E':'TRA34E','TRA 34 N':'TRA34N',
     'TRA 43 A':'TRA43A','TRA 43 W':'TRA43W','TRA 10 B':'TRA10B'}
PT=r"(\d{2})°(\d{2})'(\d{2})\"N , (\d{3})°(\d{2})'(\d{2})\"([EW])"
LV=r"(UNL|FL ?\d{3}|\d+ ?ft A[MS][SF][LC]?|\d+ ?ft ASFC|SFC|GND)"
hdr=re.compile(r"(?:LF )?\b(TRA|CBA|[RD]) (\d{1,4}(?: ?[A-Z]{1,2}\d?(?:\.\d)?)?)\b ((?:[A-ZÉÈÂÔ'\-]+ ){0,4})(?=\d{2}°|cercle)")
def lv(s):
  s=s.replace(' ','')
  if s=='UNL': return 999
  if s.startswith('FL'): return int(s[2:])
  if s in ('SFC','GND'): return 0
  return round(int(re.match(r'(\d+)ft',s)[1])/100)
def pt(m):
  la=int(m[0])+int(m[1])/60+int(m[2])/3600; lo=int(m[3])+int(m[4])/60+int(m[5])/3600
  return [round(la,4),round(-lo if m[6]=='W' else lo,4)]
heads=list(hdr.finditer(t)); out={}
for i,h in enumerate(heads):
  name=(h[1]+' '+h[2]+' '+h[3]).strip()
  if name not in SEL or SEL[name] in out: continue
  end=heads[i+1].start() if i+1<len(heads) else len(t); blk=t[h.end():min(end,h.end()+4000)]
  vm=re.search(LV+r"\s*-{6,}\s*"+LV,blk)
  if not vm: continue
  geo=blk[:vm.start()]; pts=[pt(x) for x in re.findall(PT,geo)]
  if len(pts)>1 and pts[0]==pts[-1]: pts.pop()
  out[SEL[name]]={'id':SEL[name],'name':name,'kind':'tra' if name.startswith('TRA') else 'rd','top':lv(vm[1]),'bot':lv(vm[2]),'topr':vm[1],'botr':vm[2],'pts':pts,
                  'approx':bool(re.search(r'eaux territoriales|arc |frontière',geo,re.I))}
miss=[k for k in SEL.values() if k not in out]
if miss: print('Zones non trouvées :',miss)
g=os.path.join(D,'geo.json'); geo=json.load(open(g,encoding='utf-8')); geo['milz']=list(out.values()); geo['milzSrc']='eAIP France ENR 5.1/5.2 · '+ED.split('/')[-1]
json.dump(geo,open(g,'w',encoding='utf-8'),ensure_ascii=False,separators=(',',':'))
for z in out.values(): print(z['id'],z['name'],z['botr'],'→',z['topr'],len(z['pts']),'pts','(approx)' if z['approx'] else '')
