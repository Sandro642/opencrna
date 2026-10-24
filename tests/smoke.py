"""Test de fumée headless : démarre une position, fait tourner 20 min simulées avec un « bot »
qui assume, met au XFL et transfère, puis vérifie l'absence d'erreur JS.
Prérequis : pip install playwright && playwright install chromium
Usage : python3 tests/smoke.py [US|UN|INFS|ALL|...]"""
import sys, os
from playwright.sync_api import sync_playwright
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src=open(os.path.join(R,'dist/openCRNA.html'),encoding='utf-8').read()
p=os.path.join(R,'tests/_page.html')
open(p,'w',encoding='utf-8').write('<!doctype html><html><head><meta charset="utf-8"><style>body{margin:0}[hidden]{display:none!important}</style></head><body>'+src+'</body></html>')
cfg=sys.argv[1] if len(sys.argv)>1 else 'US'
with sync_playwright() as pw:
  b=pw.chromium.launch(); pg=b.new_page(viewport={'width':1440,'height':880}); errs=[]
  pg.on('pageerror',lambda e: errs.append(str(e)))
  pg.goto('file://'+p); pg.wait_for_timeout(500)
  pg.select_option('#selConfig',cfg); pg.click('#btnStart'); pg.wait_for_timeout(300)
  r=pg.evaluate('''()=>{for(let i=0;i<2400;i++){SIM.t+=.5;for(const a of SIM.acs)stepAc(a,.5);for(const f of SIM.mil)stepFighter(f,.5);
    for(let q=SIM.queue.length-1;q>=0;q--){const e=SIM.queue[q];if(SIM.t>=e.t){SIM.queue.splice(q,1);if(SIM.acs.includes(e.a))e.fn()}}
    if(SIM.t-SIM.last1s>=1){SIM.last1s=SIM.t;tick1s();for(const a of SIM.acs){if(a.state==='offered')cmdAssume(a);
      if(a.state==='assumed'&&!a.bot){a.bot=1;cmdLevel(a,a.xfl)}if(a.state==='assumed'&&a.tte!=null&&a.tte<90&&xflOK(a))cmdTransfer(a)}}
    if(SIM.t-SIM.lastRadar>=4){SIM.lastRadar=SIM.t;radarSweep()}}
   return {t:SIM.t,avions:SIM.acs.length,score:SIM.score,traites:SIM.done,pertesSep:SIM.sepLoss,penalites:SIM.pen.map(p=>p.msg)}}''')
  pg.screenshot(path=os.path.join(R,'tests/_screenshot.png'))
  print(r); print('Erreurs JS :',errs or 'aucune'); b.close()
  sys.exit(1 if errs else 0)
