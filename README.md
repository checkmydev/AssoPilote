# AssoPilot — Démo

Démo interactive d'un assistant IA de gestion des donateurs pour association
(boîte de réception Outlook + génération de réponses IA + fiche 360° du donateur
+ données sources Salesforce/Excel). Application web autonome, déployée sur
GitHub Pages, installable comme PWA sur mobile.

**En ligne :** https://checkmydev.github.io/AssoPilote/

---

## Architecture

L'app est un **fichier unique** : tout le HTML, le CSS et le JS vivent dans
`demo-assopilot.html`. Pas de build, pas de dépendances, pas de framework — on
ouvre le fichier et ça marche. C'est volontaire : portabilité maximale et
zéro friction pour une démo.

| Fichier | Rôle |
|---|---|
| `demo-assopilot.html` | **Le code source** — déployé en tant que `index.html` |
| `sw.js` | Service worker (PWA, mode **network-first**) |
| `manifest.json` | Manifeste PWA (nom, icônes, couleurs) |
| `icon*.png` / `icon*.svg` | Icônes de l'app (PWA + favicon) |
| `assets/Logo.png` | Logo affiché dans la barre de nav |
| `assets/*.wav`, `assets/*.png` | Médias de démo (audio à transcrire, courrier scanné) |
| `deploy-assopilot.ps1` | Script de déploiement (voir ci-dessous) |

### Organisation interne de `demo-assopilot.html`
Le fichier est découpé en sections repérées par des bandeaux `═══ NOM ═══` :
`DATA` (donateurs + emails), `INBOX`, `EMAIL`, `PROFILE`, `SOURCES`, `MOBILE`,
`PWA`. Pour modifier le contenu, cherche d'abord le bon bandeau.

---

## Déploiement

> ⚠️ Deux repos distincts : le dossier local de travail **et** le repo distant
> `checkmydev/AssoPilote` (GitHub Pages). On ne clone pas le remote ; on y pousse
> les fichiers via l'API GitHub avec le script ci-dessous.

### 1. Configurer le token (une seule fois par machine)
```powershell
[Environment]::SetEnvironmentVariable("ASSOPILOT_GH_TOKEN", "ghp_xxx", "User")
```
Rouvre le terminal pour que la variable soit prise en compte.
Le token doit avoir la permission `repo` (ou `contents:write` en fine-grained).

### 2. Déployer
```powershell
./deploy-assopilot.ps1            # pousse tous les fichiers modifiés
./deploy-assopilot.ps1 -Only sw.js   # pousse un seul fichier
```
Le script calcule le hash de chaque fichier et **ne pousse que ce qui a changé**
(pas de commit vide). Mise en ligne ~1 min après le push.

---

## Notes importantes

- **Le token GitHub ne doit JAMAIS être écrit en dur** dans un fichier ou une
  commande. Toujours passer par `ASSOPILOT_GH_TOKEN`. Si un token a fuité,
  le révoquer sur https://github.com/settings/tokens et en générer un nouveau.

- **Service worker en network-first** : `sw.js` va toujours chercher la version
  fraîche en ligne et n'utilise le cache qu'en secours hors-ligne. C'est ce qui
  garantit que les mises à jour arrivent sur mobile. ⚠️ Ne **jamais** le repasser
  en « cache-first » : cela servirait éternellement une vieille version (bug
  rencontré et corrigé en juin 2026).

- **Tester sur mobile** : si un changement ne s'affiche pas, vider le cache du
  site une fois (appui long sur l'icône → Stockage → Effacer le cache/données,
  ou Chrome → Paramètres des sites → AssoPilot → Effacer). Normalement plus
  nécessaire depuis le passage en network-first.

- **Pas de framework / pas de build** : garder cette contrainte. Toute logique
  va dans `demo-assopilot.html`.
