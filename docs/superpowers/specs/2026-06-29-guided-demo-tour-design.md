# Design — Tour guidé « Visite guidée » (mode démo)

**Date :** 2026-06-29
**App :** AssoPilot (`index.html`, mono-fichier, PWA hors-ligne via `sw.js`)
**Objectif :** Un parcours d'onboarding qui explique les zones importantes de l'app à
l'aide de bulles avec flèche (style coachmark), démarrant automatiquement à la première
visite, relançable, et **skippable en un clic**.

## Décisions validées

| Sujet | Décision |
|---|---|
| Déclenchement | Auto à la 1ère visite (`localStorage`) **+** bouton de relance toujours dispo |
| Ampleur | 7 étapes ancrées + 1 carte finale centrée |
| Étapes admin-only | Affichées seulement si l'utilisateur est admin ; sinon sautées |
| Mobile | Inclus (repli sur bulle centrée quand l'ancre n'est pas visible) |
| Skip | Lien « Passer la visite » + croix ✕ + touche ESC = fermeture en un clic |
| Approche technique | Moteur « maison » en JS vanilla, intégré à `index.html` (pas de librairie externe) |
| Bouton de relance | Icône « ? » dans le header (toujours visible, non admin-only) |

## 1. Architecture

Tout est ajouté dans `index.html`, en trois blocs :

- **CSS** (préfixe `.tour-`) : overlay sombre, spotlight, bulle, flèche, contrôles.
  Réutilise les variables/teintes existantes (indigo `--i700`, cream, rayons).
- **Données** : un tableau `TOUR_STEPS`, un objet par étape.
- **Moteur** (fonctions globales) : `startTour(force)`, `tourGo(i)`, `tourNext()`,
  `tourPrev()`, `tourSkip()`, `tourFinish()`, `tourPosition()`.

### Modèle d'une étape

```js
{
  sel: '#email-list',        // sélecteur CSS de la cible (ou null pour carte centrée)
  title: '📥 Votre boîte de réception',
  body: 'Texte explicatif…',
  side: 'right',             // côté préféré : 'right'|'left'|'top'|'bottom'|'center' ; fallback auto
  adminOnly: false,          // sauté si l'utilisateur n'est pas admin
  before: () => { /* pré-action optionnelle : ouvrir un email, switch vue mobile */ }
}
```

## 2. Les étapes

| # | Cible | Titre | Texte | Pré-action | adminOnly |
|---|---|---|---|---|---|
| 1 | `#email-list` | 📥 Votre boîte de réception | « Tous les emails entrants, déjà pré-triés par l'IA. Cliquez-en un pour voir le traitement. » | `mobSel('list')` si mobile | non |
| 2 | `.det-l` | 🏷️ Classification automatique | « L'IA détecte le type de demande et son niveau de confiance — ici sans aucune saisie. » | `sel(premierEmailId)` | non |
| 3 | `.btn-gen` | ⚡ Réponse générée | « Un clic et l'assistant rédige une réponse adaptée et empathique, prête à envoyer. » | (email déjà ouvert via l'étape 2) | non |
| 4 | `#chatFab` | 💬 L'assistant | « Posez vos questions sur les emails et leur statut en langage naturel. » | — | non |
| 5 | `#btnSrc` | 🗃️ Données sources | « Salesforce et l'Excel des dons, consolidés et consultables ici. » | — | non |
| 6 | `#btnAdmin` | 📊 Pilotage | « Vue d'ensemble de l'activité de l'équipe et des gains. » | — | **oui** |
| 7 | `.savings-pill` | ⏱️ Le temps gagné | « Le ROI en clair : le temps que l'asso économise grâce à l'automatisation. » | — | **oui** |
| 8 | `null` (centré) | ✅ C'est tout ! | « Explorez librement — et relancez cette visite à tout moment via le « ? » en haut. » | — | non |

Notes :
- Les étapes pointent les **boutons** Pilotage / Données sources **sans** ouvrir les
  overlays (`adminOverlay` / `srcOverlay`) — plus robuste.
- `premierEmailId` = `EMAILS[0].id` (l'app ne sélectionne aucun email au boot : `init()`
  appelle seulement `renderList()`, `activeId` démarre à `null`). Le tour doit donc ouvrir
  un email avant les étapes 2-3.
- Pour un non-admin, les étapes 6-7 sont sautées → le tour passe de l'étape 5 à la carte
  finale 8.

## 3. Comportement UI

- **Spotlight** : overlay `rgba(0,0,0,.55)` avec un « trou » lumineux autour de la cible
  (technique `box-shadow: 0 0 0 9999px rgba(0,0,0,.55)` sur un div positionné sur le rect
  de la cible), coins arrondis ~10px, padding ~6px autour de l'élément.
- **Bulle** : carte blanche, `border-radius:14px`, ombre douce, titre indigo, texte gris
  foncé. **Flèche** triangulaire de la même couleur que le fond, orientée vers la cible.
- **Choix du côté** : on part du `side` préféré ; si la bulle déborderait du viewport, on
  bascule automatiquement vers le côté avec le plus de place. Sans cible (`sel:null`) ou
  cible invisible → bulle **centrée, sans flèche**.
- **Contrôles** (dans la bulle) : `‹ Précédent` · compteur `n / total` · `Suivant ›`
  (devient `Terminer` à la dernière étape). En haut à droite : croix ✕. En bas : lien
  discret « Passer la visite ».
- **Skip en un clic** : ✕, lien « Passer », et touche **ESC** ferment tout le tour
  immédiatement. Le clic sur le fond sombre est **neutre** (évite la fermeture accidentelle
  pendant la lecture).

## 4. Déclenchement & persistance

- Clé `localStorage["assopilot_tourSeen"] = "1"`.
- **Auto-start** : à la fin du bootstrap (au moment où le FAB chatbot devient visible,
  `bootstrap()` ~ligne 2492), si la clé est absente → `startTour(false)`.
- **Skip ou Terminer** → pose la clé. Ne se relance plus automatiquement.
- **Relance** : `startTour(true)` ignore la clé (ne la lit pas, ne la modifie pas tant que
  l'utilisateur ne re-skippe/termine pas).

## 5. Bouton de relance

- Petit bouton icône **« ? »** ajouté dans le header (`<header>`, près de `#btnSrc`), id
  `#btnTour`, `onclick="startTour(true)"`, `aria-label="Visite guidée"`. Non admin-only
  (visible pour tous). Style aligné sur `.btn-sources`.

## 6. Cas limites (robustesse)

- **Étape admin-only** : sautée quand `currentProfile.role !== 'admin'`.
- **Cible absente / masquée / hors écran** (mobile, overlay ouvert, `display:none`,
  rect de taille 0) : repli automatique → bulle centrée sans flèche, même texte.
  Aucune étape ne casse le tour.
- **Mobile** : les `before()` adaptent la vue (`mobSel`) ; sinon le repli centré s'applique.
  Le tour reste fonctionnel sous le breakpoint.
- **Resize / scroll** : `tourPosition()` est rappelée (throttle léger) pour recaler bulle +
  spotlight sur l'étape courante.
- **Avance/recul** : `tourNext`/`tourPrev` sautent les étapes non éligibles (admin-only).

## 7. Style (détails)

- Bulle : fond blanc, ombre `0 10px 30px rgba(0,0,0,.18)`, largeur ~300px (max 88vw).
- Bouton « Suivant/Terminer » : dégradé indigo (cohérent avec `.btn-gen`).
- Lien « Passer » : gris, souligné au survol.
- Spotlight & bulle au-dessus de tout (`z-index` > `chat-fab` qui est à 300, donc ~10000).

## 8. Tests (manuel — aucun framework de test dans ce projet)

Checklist à vérifier dans le navigateur :
1. Première visite (localStorage vide) → le tour démarre seul après login.
2. Terminer → recharger → le tour ne redémarre pas.
3. Skip (✕ / « Passer » / ESC) → pose la clé, ne redémarre pas.
4. Bouton « ? » → relance le tour même après l'avoir vu.
5. Étapes 2-3 : un email s'ouvre automatiquement, la bannière et « Générer » sont ciblés.
6. Admin → 7 étapes + carte finale ; non-admin → 5 étapes (6-7 sautées) + carte finale.
7. Resize de la fenêtre pendant le tour → bulle/spotlight se recalent.
8. Mobile (largeur réduite) → tour fonctionnel, repli centré quand l'ancre est cachée.

## 9. Hors périmètre (YAGNI)

- Pas de librairie externe (driver.js/Shepherd) → pas de dépendance ni de cache SW à gérer.
- Pas de tour multi-langue (FR uniquement, comme le reste de l'app).
- Pas d'ouverture automatique des overlays Pilotage/Données sources (on pointe les boutons).
- Pas de persistance « étape en cours » (un tour relancé repart de l'étape 1).
