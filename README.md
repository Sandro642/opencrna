# openCRNA

Simulateur de contrôle aérien en route (CRNA), profil LFBB Bordeaux. Version web en un seul fichier
HTML et application macOS (Electron).

## Installer (macOS Apple Silicon)
Télécharger `openCRNA-macOS-AppleSilicon.zip` dans les [Releases](https://github.com/Sandro642/opencrna/releases/latest),
glisser `openCRNA.app` dans Applications, puis `xattr -cr /Applications/openCRNA.app`.
L'app propose ensuite elle-même les nouvelles versions (menu openCRNA → Rechercher les mises à jour…).

## Jouer
- Web : ouvrir `dist/openCRNA.html` dans un navigateur.
- Mac : `./mac/build_mac.sh` puis `open mac/dist/openCRNA-darwin-arm64/openCRNA.app`
  (prérequis : Node.js 18+ et Python 3).

## Développer
1. Modifier `src/openCRNA.src.html` (ou `data/geo.json` via `data/gen_geo.py`).
2. `python3 build/build.py`
3. `python3 tests/smoke.py US` (prérequis : `pip install playwright && playwright install chromium`).

Données : VATSpy Data Project (limites, VATSIM), OurAirports (VOR, terrains). Points 5 lettres,
fréquences et limites verticales simplifiés ou fictifs. Usage ludique, pas opérationnel.
