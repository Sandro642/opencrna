#!/usr/bin/env bash
# Publie une nouvelle version : incrémente la version, reconstruit, commit et push.
# GitHub Actions construit alors l'app et crée la release ; l'app proposera la mise à jour.
#   ./release.sh "Message (affiché comme « Nouveautés » dans l'app)" [patch|minor|major]
set -euo pipefail
cd "$(dirname "$0")"
MSG=${1:?message requis}; PART=${2:-patch}
V=$(python3 - "$PART" <<'PY'
import json,sys,re
p='mac/app/package.json';s=open(p,encoding='utf-8').read()
v=[int(x) for x in json.loads(s)['version'].split('.')]
i={'major':0,'minor':1,'patch':2}[sys.argv[1]];v[i]+=1;v[i+1:]=[0]*(2-i)
n='.'.join(map(str,v));open(p,'w',encoding='utf-8').write(re.sub(r'"version": *"[^"]+"','"version": "%s"'%n,s,1));print(n)
PY
)
python3 build/build.py
git add -A
git commit -q -m "$MSG" -m "Version $V" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git push -q origin main
echo "Version $V poussée. Suivi : gh run watch \$(gh run list -L1 --json databaseId -q '.[0].databaseId')"
