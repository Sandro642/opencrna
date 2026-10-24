# openCRNA

Simulateur de contrôle aérien **en route** (façon CRNA français), inspiré d'openScope mais centré sur
des secteurs de contrôle au lieu d'un aéroport. Premier profil : **LFBB, CRNA Sud-Ouest (Bordeaux)**.
Interface et textes en **français**. Le joueur tient une position radar : il assume les vols transférés
par les secteurs voisins, les sépare (5 NM / 1 000 ft), les amène au niveau de sortie coordonné (XFL)
et les transfère au secteur suivant.

Deux cibles construites à partir d'**un seul fichier source** :
- **Web** : `dist/openCRNA.html`, publié comme artifact claude.ai (page HTML autonome).
- **macOS** : app Electron dans `mac/` (Apple Silicon, signature ad hoc).

## Publication et mises à jour (app macOS)

Dépôt public **github.com/Sandro642/opencrna**, branche `main`. **Après chaque modification demandée
par l'utilisateur** : build + smoke test si possible, puis `./release.sh "Message en français" [patch|minor|major]`
(incrémente `mac/app/package.json`, rebuild, commit, push). Le workflow `.github/workflows/release.yml`
(runner macos-14) construit l'app et crée la release `vX.Y.Z` avec le zip et `dist/openCRNA.html`.
Le message de commit devient les « Nouveautés » affichées dans l'app : l'écrire pour l'utilisateur.
L'app (`mac/app/updater.js`) vérifie la dernière release 4 s après le lancement (et via le menu
openCRNA → Rechercher les mises à jour…), télécharge le zip, remplace le bundle et relance.
Pas de Squirrel/electron-updater : impossible sans signature Apple. Node n'est pas installé localement.
Claude Code tourne en root : toute app copiée dans /Applications doit être rendue à l'utilisateur
(`chown -R sandrombp:staff /Applications/openCRNA.app`), sinon l'updater ne peut pas la remplacer.

## Arborescence

```
src/openCRNA.src.html   Tout le jeu : CSS + HTML + JS dans un seul fichier. Contient le marqueur __GEO__.
data/geo.json           Géographie (secteurs LFBB, FIR voisines, VOR, terrains) injectée à la place de __GEO__.
data/gen_geo.py         Régénère geo.json depuis OurAirports + VATSpy (téléchargement).
build/build.py          src + geo -> dist/openCRNA.html (web) et mac/app/index.html (Electron, polices locales).
mac/app/                main.js (fenêtre, menus FR), updater.js (mises à jour GitHub), package.json (version), fonts/ (woff2 JetBrains Mono, Barlow Semi Condensed).
mac/icon.icns|png       Icône (scope radar gris).
release.sh              Incrémente la version, build, commit, push (déclenche la release).
.github/workflows/       release.yml : build macOS + release GitHub à chaque push sur main.
mac/build_mac.sh        Build + packaging Electron 33.4.11 darwin-arm64 + signature ad hoc + zip.
tests/smoke.py          Test headless Playwright : 20 min simulées avec un bot, échoue s'il y a une erreur JS.
dist/openCRNA.html      Dernière version web construite.
```

## Commandes

```bash
python3 build/build.py            # toujours après une modif de src/ ou data/
python3 tests/smoke.py US         # aussi : UN, UNUS, INFS, INFN, ALL, X, R, Z, N, H, L, T, P
./mac/build_mac.sh                # produit mac/dist/openCRNA-macOS-AppleSilicon.zip
open mac/dist/openCRNA-darwin-arm64/openCRNA.app
```

Dans la page, l'état est global : `SIM`, `VOL`, `sel`, fonctions `stepAc`, `tick1s`, `trySpawn`,
`spawnConverging`, `cmdLevel`… sont accessibles via `page.evaluate` pour tester.

## Architecture du JS (sections `/* ===== … ===== */` dans le source)

- **Géométrie** : projection locale équirectangulaire en NM centrée 45°N / 0,9°E (`P(lat,lon)`), polygones `mkPoly`, `inPoly`.
- **Atmosphère ISA** : `casToTas`, `machToCas`, `sos` ; croisement IAS/Mach réaliste.
- **Performances** (`PERF`) : par type OACI, taux de montée interpolé selon l'altitude, plafond, IAS/Mach montée-croisière-descente, sillage.
- **Compagnies** (`AL`) : indicatifs radio, flottes, formats d'indicatif ; `fr:1` → phraséologie française.
- **Points** (`PTS`) : VOR réels + terrains + points 5 lettres **fictifs** (`FIXDEF`).
- **Unités voisines** (`UNITS`, `SECFREQ`, `APPS`) : fréquences **fictives**.
- **Configurations** (`CONFIGS`) : secteurs VATSpy LFBB (H, L, N, P, R, T, X, Z inférieurs FL115–345 ; UN, US supérieurs FL345–660 ; regroupements).
- **Flux** (`FLOWDEF`) : ~30 routes réalistes avec origines/destinations, compagnies, plage de RFL ; inverses générés automatiquement.
- **Vent** : courant-jet uniforme dont la force dépend de l'altitude.
- **Modèle avion** : `stepAc(a,dt)` (vertical avec capture, vitesse, virage taux limité par l'inclinaison de 25°, navigation avec correction de vent, séquencement des points) ; `plannedCfl` = profil plan de vol (montée RFL, descente 3:1 vers l'arrivée).
- **Prédiction** : `predict(a)` clone l'avion et simule par pas de 5 s ; `analyze(a,S)` trouve entrée/sortie du volume → `efl/eflKind`, `xfl/xflKind` (level/climb/desc), unité précédente/suivante (`unitAt`).
- **Création** : `trySpawn('c'|'b', tau)` vols concernés ou de fond, déconflictés avant l'entrée ; `adopt()` ; `maybeNordo()` ; `spawnConverging()` injecte un vol qui croise un vol pré-annoncé au même niveau dans le volume.
- **États d'un vol** : `bg` (non concerné) → `pre` (pré-annoncé, `preT`) → `offered` (transféré vers moi, `offerT`) → `assumed` → `transferred` ; `missed` si jamais pris. Annulation de transfert possible (`canRetake` : encore dans le volume ou < 90 s, pas un transfert auto).
- **Radio** : `atc()`, `pilot()`, `queue(a,delay,fn)` (réponse pilote différée ; si `a.silent` → `noResponse`).
- **COMLOSS / défense aérienne** : `a.nordo {kind:'never'|'mid', onset}`, `a.silent`, `cmdGuard` (121.5, 40 % de réussite une fois), `askAlert/cmdAlert`, `processAlerts` (étapes 0→5, 9 = terminé), chasseurs `SIM.mil` avec `stepFighter` (poursuite, supersonique, escorte, retour Mont-de-Marsan LFBM).
- **Clairances** : `cmdLevel`, `cmdHdg`, `cmdDirect`, `cmdResume`, `cmdSpeed`, `cmdAssume`, `askTransfer/cmdTransfer` (confirmation), `askRetake/cmdRetake`.
- **Boucle** : pas physique 0,5 s ; `tick1s` (états, pénalités, demandes pilotes, séparation, génération) ; balayage radar toutes les 4 s (`radarSweep`, positions affichées = `a.plot`) ; `autoLabels` place les étiquettes.
- **Séparation** : `checkSeparation` (perte < 5 NM et < 950 ft, STCA par extrapolation à 120 s) ; ne compte que si un des vols est « à moi » (`isMine`).
- **Écran radar** : canvas, `draw()`, `drawTraffic()`, `labelLines()` (champs cliquables `cs`, `cfl`, `nav`, `spd`), `drawShape()` (forme selon la destination, `destCat`), plancher/plafond au centre du volume, `drawMil()`.
- **Outils** : mesure (clic droit + glisser), **Trajectoires** (`pairAnalysis`, `avoidance`, carte `#confCard`) : croisement, CPA, verdict DANGER/ATTENTION/SÛR, résolutions en un clic.
- **UI** : strips (Entrants ambre / Sous contrôle vert / Transférés bleu / Défense aérienne), fiche vol, menus contextuels, ligne de commande (`runCmd`), réglages en `localStorage` (`opencrna.v1`).

## Conventions et choix déjà validés par l'utilisateur

- Thème **noir et gris** ; seules couleurs : ambre = entrants, vert = sous contrôle, bleu = transférés, rouge = alertes (STCA, perte de séparation, COMLOSS).
- Forme du symbole radar = destination : ▽ arrivée région LFBB, ○ France, ◇ Espagne/Portugal/Canaries, □ Royaume-Uni/Irlande, ⬡ reste de l'Europe, ☆ long-courrier, ▲ plein = Rafale PO. Point plein = vol sous mon contrôle.
- Transfert et reprise de transfert **toujours avec confirmation**. Alerte défense aérienne aussi.
- Plancher et plafond affichés au centre de la zone contrôlée.
- Les données « réelles » : limites VATSpy (approximation), VOR OurAirports. Le reste est simplifié/fictif et doit le rester **clairement indiqué** dans l'aide (points 5 lettres, fréquences, limites verticales).
- Contraintes artifact claude.ai (version web) : un seul fichier, polices uniquement via Google Fonts, pas d'`alert/confirm/prompt`, `localStorage` dans des try/catch, scripts externes seulement depuis les CDN autorisés (aucun utilisé actuellement).
- Le source utilise des lignes JS très denses (minifiées à la main). Préférer des modifications ciblées ; vérifier avec `tests/smoke.py` après chaque changement.

## Pistes non faites (idées évoquées ou naturelles)

- Autres profils : LFMM, LFRR, LFFF, LFEE (déjà annoncés « à venir » dans le menu de démarrage) — il faudrait des FLOWDEF et points par centre et un sélecteur de profil réel.
- Vraie base de points/routes (AIRAC) au lieu des points fictifs.
- Build Intel (x64) ou universel ; signature/notarisation Apple avec un compte développeur.
- Coordination téléphonique avec les secteurs voisins (demander un niveau de sortie différent).
