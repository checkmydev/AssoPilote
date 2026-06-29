# Guided Demo Tour Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an in-app guided tour (coachmark bubbles with arrows) that auto-starts on first visit, is relaunchable from a header button, and is skippable in one click.

**Architecture:** A self-contained vanilla-JS tour engine added to `index.html` — a CSS block (overlay/spotlight/bubble/arrow), a `TOUR_STEPS` data array, engine functions (`startTour`, `tourGo`, `tourRender`, `_placeBubble`, nav/skip/finish), a header relaunch button, and an auto-start hook in `bootstrap()`. Steps point at existing elements by selector; admin-only steps are filtered out for non-admins; any step whose target is hidden/offscreen falls back to a centered bubble.

**Tech Stack:** Plain HTML/CSS/JS inside the single-file `index.html`. No external library. No test framework exists in this project, so each task is verified manually in the browser.

---

## File Structure

All changes are in **`index.html`** (single-file app):
- **CSS block** (inside `<style>`, before `</style>` at line 590): `.tour-*` and `.btn-tour` rules.
- **Header markup** (after `#btnSrc`, line 649): the `#btnTour` relaunch button.
- **Tour overlay markup** (before `</body>`, near `#chatFab` at line 3184).
- **JS** (after the `mobInit`/`isMob` helpers area, ~line 1825): `TOUR_STEPS`, engine functions.
- **Auto-start hook** (in `bootstrap()`, after line 2492).

Reference facts (verified):
- `EMAILS` is a global array; `EMAILS[0].id` is the first email's id. `sel(id)` opens an email and (on mobile) switches to the `'main'` view.
- `isMob()` = `innerWidth <= 767`. Mobile view tabs: `'inbox'`, `'main'`, `'profile'`.
- `.btn-sources` is `display:none` on mobile (line 435) — the relaunch button must NOT rely on that class to stay visible.
- `currentProfile.role === 'admin'` distinguishes admin users. `--i700` is the indigo CSS variable already used by `.chat-fab:hover`.

---

### Task 1: Tour CSS

**Files:**
- Modify: `index.html` (insert before `</style>`, line 590)

- [ ] **Step 1: Add the CSS block**

Insert immediately before the `</style>` line (590):

```css
    /* ─── Tour guidé ─────────────────────────────────────── */
    .tour-mask{position:fixed;inset:0;z-index:10000;display:none}
    .tour-mask.show{display:block}
    .tour-hole{position:absolute;border-radius:10px;box-shadow:0 0 0 9999px rgba(15,23,42,.55);
      transition:left .2s,top .2s,width .2s,height .2s;pointer-events:none}
    .tour-arrow{position:absolute;z-index:10001;width:14px;height:14px;background:#fff;
      transform:rotate(45deg);box-shadow:-2px -2px 4px rgba(0,0,0,.04)}
    .tour-bub{position:fixed;z-index:10002;width:300px;max-width:88vw;background:#fff;border-radius:14px;
      box-shadow:0 10px 30px rgba(0,0,0,.18);padding:16px 16px 12px;font-family:inherit;color:#1e293b}
    .tour-bub h4{margin:0 0 6px;font-size:.95rem;color:var(--i700,#4338ca)}
    .tour-bub p{margin:0 0 12px;font-size:.84rem;line-height:1.45;color:#475569}
    .tour-row{display:flex;align-items:center;justify-content:space-between;gap:8px}
    .tour-count{font-size:.72rem;color:#94a3b8}
    .tour-btns{display:flex;gap:6px}
    .tour-prev,.tour-next{border:none;border-radius:7px;padding:.4rem .7rem;font-size:.78rem;
      font-weight:600;cursor:pointer;font-family:inherit}
    .tour-prev{background:#f1f5f9;color:#475569}
    .tour-next{background:var(--i700,#4338ca);color:#fff}
    .tour-skip{display:block;margin-top:10px;background:none;border:none;color:#94a3b8;
      font-size:.74rem;cursor:pointer;text-decoration:underline;font-family:inherit;padding:0}
    .tour-x{position:absolute;top:8px;right:10px;background:none;border:none;color:#94a3b8;
      font-size:1rem;cursor:pointer;line-height:1}
    .btn-tour{display:flex;align-items:center;justify-content:center;width:30px;height:30px;
      background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);color:rgba(255,255,255,.85);
      border-radius:6px;font-size:.85rem;font-weight:700;cursor:pointer;font-family:inherit;
      transition:background .15s}
    .btn-tour:hover{background:rgba(255,255,255,.2)}
    @media(max-width:767px){ .btn-tour{display:flex} }
```

- [ ] **Step 2: Verify the file still loads**

Open `index.html` in a browser. Expected: no console errors, app renders normally (the new CSS targets elements that don't exist yet, so nothing visible changes).

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "feat(tour): add guided-tour CSS (overlay, spotlight, bubble, relaunch button)"
```

---

### Task 2: Header relaunch button + tour overlay markup

**Files:**
- Modify: `index.html` (after `#btnSrc`, line 649; and before `</body>` near `#chatFab`, line 3184)

- [ ] **Step 1: Add the relaunch button to the header**

After the `#btnSrc` button (line 649), insert:

```html
  <button class="btn-tour" id="btnTour" onclick="startTour(true)" title="Visite guidée" aria-label="Visite guidée">?</button>
```

- [ ] **Step 2: Add the tour overlay markup**

Immediately before the `#chatFab` button line (3184, `<button class="chat-fab" ...>`), insert:

```html
<div class="tour-mask" id="tourMask">
  <div class="tour-hole" id="tourHole"></div>
  <div class="tour-arrow" id="tourArrow"></div>
  <div class="tour-bub" id="tourBub">
    <button class="tour-x" onclick="tourSkip()" aria-label="Fermer">✕</button>
    <h4 id="tourTitle"></h4>
    <p id="tourBody"></p>
    <div class="tour-row">
      <span class="tour-count" id="tourCount"></span>
      <div class="tour-btns">
        <button class="tour-prev" id="tourPrevBtn" onclick="tourPrev()">‹ Précédent</button>
        <button class="tour-next" id="tourNextBtn" onclick="tourNext()">Suivant ›</button>
      </div>
    </div>
    <button class="tour-skip" onclick="tourSkip()">Passer la visite</button>
  </div>
</div>
```

- [ ] **Step 3: Verify in browser**

Reload. Expected: a small `?` button appears in the header. Clicking it does nothing yet AND logs `ReferenceError: startTour is not defined` in the console — that is expected (the engine arrives in Task 4). The tour overlay is present but hidden (`display:none`).

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat(tour): add header relaunch button and tour overlay markup"
```

---

### Task 3: Tour data and step-eligibility helper

**Files:**
- Modify: `index.html` (insert after the `mobInit()` function, which ends around line 1845 — place the block just before the `// ═══ EMAIL VIEW ═══` style section or any clear function boundary in that region)

- [ ] **Step 1: Add the `TOUR_STEPS` array, state, and eligibility helper**

Insert this block in the JS area after the mobile helpers (after `mobInit()` / `isMob()`):

```js
// ═══════════════════════════ TOUR GUIDÉ ═══════════════════════════
const TOUR_STEPS = [
  { sel:'#email-list', side:'right',
    title:'📥 Votre boîte de réception',
    body:'Tous les emails entrants, déjà pré-triés par l\'IA. Cliquez-en un pour voir le traitement.',
    before:()=>{ if(isMob()) mobSel('inbox'); } },
  { sel:'.det-l', side:'bottom',
    title:'🏷️ Classification automatique',
    body:'L\'IA détecte le type de demande et son niveau de confiance — ici sans aucune saisie.',
    before:()=>{ if(typeof EMAILS!=='undefined' && EMAILS.length) sel(EMAILS[0].id); } },
  { sel:'.btn-gen', side:'top',
    title:'⚡ Réponse générée',
    body:'Un clic et l\'assistant rédige une réponse adaptée et empathique, prête à envoyer.' },
  { sel:'#chatFab', side:'left',
    title:'💬 L\'assistant',
    body:'Posez vos questions sur les emails et leur statut en langage naturel.' },
  { sel:'#btnSrc', side:'bottom',
    title:'🗃️ Données sources',
    body:'Salesforce et l\'Excel des dons, consolidés et consultables ici.' },
  { sel:'#btnAdmin', side:'bottom', adminOnly:true,
    title:'📊 Pilotage',
    body:'Vue d\'ensemble de l\'activité de l\'équipe et des gains.' },
  { sel:'.savings-pill', side:'bottom', adminOnly:true,
    title:'⏱️ Le temps gagné',
    body:'Le ROI en clair : le temps que l\'association économise grâce à l\'automatisation.' },
  { sel:null, side:'center',
    title:'✅ C\'est tout !',
    body:'Explorez librement — et relancez cette visite à tout moment via le « ? » en haut.' }
];
let _tourList = [], _tourIdx = 0, _trpTimer = null;

function tourEligible(){
  const admin = currentProfile && currentProfile.role === 'admin';
  return TOUR_STEPS.filter(s => !s.adminOnly || admin);
}
```

- [ ] **Step 2: Verify in browser console**

Reload, then in the console run: `tourEligible().length`
Expected (logged in as admin): `8`. As a non-admin (`currentProfile.role !== 'admin'`): `6`.

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "feat(tour): add TOUR_STEPS data and admin eligibility filter"
```

---

### Task 4: Tour engine — start, render, positioning

**Files:**
- Modify: `index.html` (append after the `tourEligible()` function from Task 3)

- [ ] **Step 1: Add the visibility helper and bubble placement**

Append after `tourEligible()`:

```js
function _tourVisible(el){
  if(!el) return false;
  const r = el.getBoundingClientRect();
  if(r.width === 0 && r.height === 0) return false;
  const cs = getComputedStyle(el);
  if(cs.display === 'none' || cs.visibility === 'hidden') return false;
  return r.bottom > 0 && r.right > 0 && r.top < innerHeight && r.left < innerWidth;
}

function _placeBubble(bub, arrow, r, side){
  bub.style.transform = 'none';
  const bw = bub.offsetWidth, bh = bub.offsetHeight, gap = 14, vw = innerWidth, vh = innerHeight;
  let s = side;
  const space = { right: vw - r.right, left: r.left, top: r.top, bottom: vh - r.bottom };
  if(s === 'right'  && space.right  < bw + gap) s = space.left   > space.right  ? 'left' : 'bottom';
  if(s === 'left'   && space.left   < bw + gap) s = space.right  > space.left   ? 'right' : 'bottom';
  if(s === 'bottom' && space.bottom < bh + gap) s = 'top';
  if(s === 'top'    && space.top    < bh + gap) s = 'bottom';
  let left, top;
  if(s === 'right')      { left = r.right + gap;        top = r.top + r.height/2 - bh/2; }
  else if(s === 'left')  { left = r.left - gap - bw;    top = r.top + r.height/2 - bh/2; }
  else if(s === 'top')   { left = r.left + r.width/2 - bw/2; top = r.top - gap - bh; }
  else                   { left = r.left + r.width/2 - bw/2; top = r.bottom + gap; }
  left = Math.max(8, Math.min(left, vw - bw - 8));
  top  = Math.max(8, Math.min(top,  vh - bh - 8));
  bub.style.left = left + 'px';
  bub.style.top  = top  + 'px';
  arrow.style.display = 'block';
  if(s === 'right')      { arrow.style.left = (r.right + gap - 7) + 'px';      arrow.style.top = (r.top + r.height/2 - 7) + 'px'; }
  else if(s === 'left')  { arrow.style.left = (r.left - gap - 7) + 'px';       arrow.style.top = (r.top + r.height/2 - 7) + 'px'; }
  else if(s === 'top')   { arrow.style.left = (r.left + r.width/2 - 7) + 'px'; arrow.style.top = (r.top - gap - 7) + 'px'; }
  else                   { arrow.style.left = (r.left + r.width/2 - 7) + 'px'; arrow.style.top = (r.bottom + gap - 7) + 'px'; }
}
```

- [ ] **Step 2: Add `tourRender` and `tourGo`**

Append:

```js
function tourRender(step){
  const hole  = document.getElementById('tourHole');
  const bub   = document.getElementById('tourBub');
  const arrow = document.getElementById('tourArrow');
  const el = step.sel ? document.querySelector(step.sel) : null;
  document.getElementById('tourTitle').textContent = step.title;
  document.getElementById('tourBody').textContent  = step.body;
  document.getElementById('tourCount').textContent = (_tourIdx + 1) + ' / ' + _tourList.length;
  document.getElementById('tourNextBtn').textContent = (_tourIdx === _tourList.length - 1) ? 'Terminer' : 'Suivant ›';
  document.getElementById('tourPrevBtn').style.visibility = (_tourIdx === 0) ? 'hidden' : 'visible';
  if(_tourVisible(el)){
    const r = el.getBoundingClientRect();
    hole.style.display = 'block';
    hole.style.left = (r.left - 6) + 'px';
    hole.style.top  = (r.top - 6) + 'px';
    hole.style.width  = (r.width + 12) + 'px';
    hole.style.height = (r.height + 12) + 'px';
    _placeBubble(bub, arrow, r, step.side === 'center' ? 'bottom' : step.side);
  } else {
    hole.style.display = 'none';
    arrow.style.display = 'none';
    bub.style.left = '50%';
    bub.style.top  = '50%';
    bub.style.transform = 'translate(-50%,-50%)';
  }
}

function tourGo(i){
  if(i < 0 || i >= _tourList.length) return;
  _tourIdx = i;
  const step = _tourList[i];
  if(step.before){ try{ step.before(); }catch(e){} }
  setTimeout(()=>tourRender(step), 60);  // let before() re-render the DOM first
}
```

- [ ] **Step 3: Add `startTour`**

Append:

```js
function startTour(force){
  if(!force && localStorage.getItem('assopilot_tourSeen')) return;
  _tourList = tourEligible();
  _tourIdx = 0;
  if(!_tourList.length) return;
  document.getElementById('tourMask').classList.add('show');
  document.addEventListener('keydown', _tourKey);
  window.addEventListener('resize', _tourReposition);
  window.addEventListener('scroll', _tourReposition, true);
  tourGo(0);
}
```

(The `_tourKey` and `_tourReposition` handlers are added in Task 5; this step references them but they are only invoked at runtime, so the file still parses.)

- [ ] **Step 4: Verify partial engine in browser console**

Reload. In the console run: `_tourList = tourEligible(); _tourIdx = 0; document.getElementById('tourMask').classList.add('show'); tourGo(0);`
Expected: the dark overlay appears with a spotlight on the inbox list and a bubble titled "📥 Votre boîte de réception" with an arrow. (Navigation buttons won't advance yet — that's Task 5.) Then run `document.getElementById('tourMask').classList.remove('show')` to dismiss.

- [ ] **Step 5: Commit**

```bash
git add index.html
git commit -m "feat(tour): add engine core — start, render, spotlight, bubble positioning"
```

---

### Task 5: Navigation, skip, finish, persistence, listeners

**Files:**
- Modify: `index.html` (append after `startTour()` from Task 4)

- [ ] **Step 1: Add navigation, finish, and listener handlers**

Append:

```js
function tourNext(){
  if(_tourIdx >= _tourList.length - 1) return tourFinish();
  tourGo(_tourIdx + 1);
}
function tourPrev(){ tourGo(_tourIdx - 1); }
function tourSkip(){ tourFinish(); }
function tourFinish(){
  localStorage.setItem('assopilot_tourSeen', '1');
  document.getElementById('tourMask').classList.remove('show');
  document.removeEventListener('keydown', _tourKey);
  window.removeEventListener('resize', _tourReposition);
  window.removeEventListener('scroll', _tourReposition, true);
}
function _tourKey(e){ if(e.key === 'Escape') tourSkip(); }
function _tourReposition(){
  clearTimeout(_trpTimer);
  _trpTimer = setTimeout(()=>{ if(_tourList[_tourIdx]) tourRender(_tourList[_tourIdx]); }, 80);
}
```

- [ ] **Step 2: Verify full navigation in browser**

Reload. Click the header `?` button. Expected, in order:
1. Tour starts at step 1 (inbox), `1 / 8` shown (admin) and `Précédent` hidden.
2. `Suivant ›` → step 2 opens the first email and spotlights the "Type détecté" banner.
3. Continue through all steps; the last shows `Terminer`.
4. `Terminer` closes the tour.
5. Reopen via `?` and press `ESC` → closes immediately.
6. Reopen via `?` and click `✕` or "Passer la visite" → closes immediately.
7. While a step is shown, resize the window → bubble + spotlight recalc to the target.

- [ ] **Step 3: Verify persistence**

In console run `localStorage.getItem('assopilot_tourSeen')` after finishing → expected `"1"`.
Run `localStorage.removeItem('assopilot_tourSeen')` to reset for the next task.

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat(tour): add navigation, skip/finish, persistence, ESC + resize handling"
```

---

### Task 6: Auto-start on first visit + full verification

**Files:**
- Modify: `index.html` (in `bootstrap()`, after line 2492 — the `chatFab` display line)

- [ ] **Step 1: Add the auto-start hook**

Immediately after the line `const _cf = document.getElementById('chatFab'); if(_cf) _cf.style.display = 'flex';` (line 2492), insert:

```js
  startTour(false);
```

- [ ] **Step 2: Verify first-visit auto-start**

In console run `localStorage.removeItem('assopilot_tourSeen')`, then reload and log in (or reload if already authenticated). Expected: the tour starts automatically once the app is ready.

- [ ] **Step 3: Verify it does not re-trigger**

Finish or skip the tour, then reload. Expected: the tour does NOT auto-start. The `?` button still relaunches it.

- [ ] **Step 4: Verify admin vs non-admin**

As admin: tour shows `… / 8` and includes Pilotage + Économisé steps. As a non-admin user (`currentProfile.role !== 'admin'`): tour shows `… / 6`, skipping those two; the final card still appears.

- [ ] **Step 5: Verify mobile fallback**

Narrow the window below 768px (or use device emulation) and relaunch via `?`. Expected: the tour runs; for steps whose target is hidden on mobile (Données sources / Pilotage buttons, hidden by the line-435 rule), the bubble appears centered with no arrow and the correct text. The `?` button itself remains visible on mobile.

- [ ] **Step 6: Commit**

```bash
git add index.html
git commit -m "feat(tour): auto-start guided tour on first visit"
```

---

## Self-Review

**Spec coverage:**
- Auto-start first visit + relaunch button → Task 6 (hook) + Task 2 (`#btnTour`). ✓
- 7 anchored steps + final card → Task 3 `TOUR_STEPS` (8 entries). ✓
- Admin-only gating → Task 3 `tourEligible()`, verified Task 6 Step 4. ✓
- Mobile fallback → `_tourVisible` + centered branch in `tourRender` (Task 4), verified Task 6 Step 5. ✓
- One-click skip (✕ / link / ESC) → Task 5. ✓
- Spotlight + bubble + arrow, auto side-flip → Task 1 (CSS) + Task 4 (`_placeBubble`). ✓
- Persistence `assopilot_tourSeen` → Task 5 `tourFinish`. ✓
- Steps 2-3 require opening an email → Task 3 step 2 `before: sel(EMAILS[0].id)`. ✓
- Pointing at buttons without opening overlays → steps 5-6 target `#btnSrc`/`#btnAdmin`, no overlay calls. ✓

**Placeholder scan:** No TBD/TODO; all code blocks complete. ✓

**Type/name consistency:** `startTour`, `tourGo`, `tourRender`, `tourNext`, `tourPrev`, `tourSkip`, `tourFinish`, `_tourKey`, `_tourReposition`, `_tourVisible`, `_placeBubble`, `tourEligible`, and the element IDs (`tourMask`, `tourHole`, `tourArrow`, `tourBub`, `tourTitle`, `tourBody`, `tourCount`, `tourPrevBtn`, `tourNextBtn`, `btnTour`) are used consistently across tasks. ✓

**Note on TDD:** This project has no JS test harness; per the spec, verification is manual in-browser. Each task ends with a concrete browser check before its commit.
