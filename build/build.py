"""Construit les deux cibles à partir de src/openCRNA.src.html + data/geo.json.
  python3 build/build.py          -> dist/openCRNA.html (version web / artifact, polices Google Fonts)
                                  -> mac/app/index.html  (version Electron, polices locales, CSP stricte)
"""
import os, re
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src=open(os.path.join(R,'src/openCRNA.src.html'),encoding='utf-8').read()
geo=open(os.path.join(R,'data/geo.json'),encoding='utf-8').read()
web=src.replace('__GEO__',geo)
os.makedirs(os.path.join(R,'dist'),exist_ok=True)
open(os.path.join(R,'dist/openCRNA.html'),'w',encoding='utf-8').write(web)
# Version Electron : pas de réseau, polices embarquées
m=re.sub(r'<link rel="preconnect"[^>]*>\n','',web)
m=re.sub(r'<link rel="stylesheet" href="https://fonts.googleapis.com[^>]*>\n','',m)
ff=''.join("@font-face{font-family:'%s';font-style:normal;font-weight:%d;font-display:swap;src:url(fonts/%s-latin-%d-normal.woff2) format('woff2')}\n"%(fam,w,fn,w)
  for fam,fn,ws in [('JetBrains Mono','jetbrains-mono',[400,600]),('Barlow Semi Condensed','barlow-semi-condensed',[400,500,600,700])] for w in ws)
m=m.replace('<style>\n','<style>\n'+ff,1).replace("--f-mono:'JetBrains Mono',ui-monospace,","--f-mono:'JetBrains Mono','SF Mono',Menlo,ui-monospace,")
html='''<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'">
<style>:root{color-scheme:dark}body{margin:0;-webkit-user-select:none;user-select:none}input,textarea{-webkit-user-select:text;user-select:text}[hidden]{display:none!important}img{max-width:100%}</style>
</head><body>
'''+m+'\n</body></html>\n'
open(os.path.join(R,'mac/app/index.html'),'w',encoding='utf-8').write(html)
print('OK : dist/openCRNA.html et mac/app/index.html')
