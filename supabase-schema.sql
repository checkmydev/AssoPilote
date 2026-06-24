-- ============================================================
--  AssoPilot — Schéma DÉDIÉ 'assopilot'
--  Projet : wzrcrszfubjsfoaxatvo (partagé avec l'app BodyCoaching)
--  Tout AssoPilot vit dans le schéma 'assopilot' => AUCUNE collision
--  avec les tables de l'autre app (qui sont dans 'public').
--
--  ⚠️ APRÈS avoir exécuté ce fichier :
--    Dashboard → Project Settings → API → "Exposed schemas"
--    → ajoute "assopilot" → Save   (sinon l'app ne voit pas les tables)
-- ============================================================

create schema if not exists assopilot;

-- Accès au schéma pour l'API PostgREST (la RLS protège les lignes)
grant usage on schema assopilot to anon, authenticated;
alter default privileges in schema assopilot grant select, insert, update, delete on tables to anon, authenticated;
alter default privileges in schema assopilot grant usage, select on sequences to anon, authenticated;
alter default privileges in schema assopilot grant execute on functions to anon, authenticated;

-- ───────────────────────────────────────────────────────────
-- 1) MEMBERS  (identité + rôle, propres à AssoPilot)
-- ───────────────────────────────────────────────────────────
create table if not exists assopilot.members (
  id             uuid primary key references auth.users(id) on delete cascade,
  email          text,
  full_name      text,
  role           text not null default 'user' check (role in ('admin','user')),
  created_at     timestamptz not null default now(),
  last_active_at timestamptz
);

-- Helper : l'utilisateur courant est-il admin AssoPilot ?
create or replace function assopilot.is_admin()
returns boolean language sql security definer set search_path = assopilot, public stable as $$
  select exists (select 1 from assopilot.members where id = auth.uid() and role = 'admin');
$$;

-- Dernière activité (RPC => pas d'UPDATE direct => anti-escalade de rôle)
create or replace function assopilot.touch_last_active()
returns void language sql security definer set search_path = assopilot, public as $$
  update assopilot.members set last_active_at = now() where id = auth.uid();
$$;

-- ───────────────────────────────────────────────────────────
-- 2) ACTIONS  (journal PRIVÉ : stats + audit)
-- ───────────────────────────────────────────────────────────
create table if not exists assopilot.actions (
  id            bigint generated always as identity primary key,
  user_id       uuid not null default auth.uid() references auth.users(id) on delete cascade,
  action_type   text not null check (action_type in
                  ('reply_generated','address_update','status_change','email_update')),
  email_id      int,
  donor_id      int,
  minutes_saved numeric not null default 0,
  details       jsonb,
  created_at    timestamptz not null default now()
);
create index if not exists ap_actions_user_idx on assopilot.actions(user_id);
create index if not exists ap_actions_created_idx on assopilot.actions(created_at desc);

-- ───────────────────────────────────────────────────────────
-- 3) SHARED_STATE  (état PARTAGÉ : modifs de fiches + emails traités)
-- ───────────────────────────────────────────────────────────
create table if not exists assopilot.shared_state (
  id          bigint generated always as identity primary key,
  kind        text not null check (kind in ('donor_patch','email_handled')),
  donor_id    int,
  email_id    int,
  patch       jsonb,
  created_by  uuid default auth.uid() references auth.users(id) on delete set null,
  created_at  timestamptz not null default now()
);
create index if not exists ap_shared_kind_idx on assopilot.shared_state(kind);

-- ───────────────────────────────────────────────────────────
-- 4) ROW LEVEL SECURITY
-- ───────────────────────────────────────────────────────────
alter table assopilot.members      enable row level security;
alter table assopilot.actions      enable row level security;
alter table assopilot.shared_state enable row level security;

-- members : lecture de son profil (ou tous si admin) ; création de son propre profil ; pas d'UPDATE (anti-escalade)
drop policy if exists members_select on assopilot.members;
create policy members_select on assopilot.members
  for select using (id = auth.uid() or assopilot.is_admin());

drop policy if exists members_insert_self on assopilot.members;
create policy members_insert_self on assopilot.members
  for insert with check (id = auth.uid());

-- L'admin peut créer / modifier le rôle / retirer des membres
drop policy if exists members_insert_admin on assopilot.members;
create policy members_insert_admin on assopilot.members
  for insert with check (assopilot.is_admin());

drop policy if exists members_update_admin on assopilot.members;
create policy members_update_admin on assopilot.members
  for update using (assopilot.is_admin()) with check (assopilot.is_admin());

drop policy if exists members_delete_admin on assopilot.members;
create policy members_delete_admin on assopilot.members
  for delete using (assopilot.is_admin());

-- actions : on insère les siennes ; on lit les siennes (ou toutes si admin)
drop policy if exists actions_insert_own on assopilot.actions;
create policy actions_insert_own on assopilot.actions
  for insert with check (user_id = auth.uid());

drop policy if exists actions_select_own_or_admin on assopilot.actions;
create policy actions_select_own_or_admin on assopilot.actions
  for select using (user_id = auth.uid() or assopilot.is_admin());

-- shared_state : tout utilisateur connecté lit et insère (données d'asso partagées)
drop policy if exists shared_select_auth on assopilot.shared_state;
create policy shared_select_auth on assopilot.shared_state
  for select using (auth.uid() is not null);

-- Données d'asso partagées : tout utilisateur connecté peut écrire (created_by est informatif).
drop policy if exists shared_insert_own  on assopilot.shared_state;
drop policy if exists shared_insert_auth on assopilot.shared_state;
create policy shared_insert_auth on assopilot.shared_state
  for insert with check (auth.uid() is not null);

-- Réinitialisation de la démo : seul l'admin peut supprimer
drop policy if exists actions_delete_admin on assopilot.actions;
create policy actions_delete_admin on assopilot.actions
  for delete using (assopilot.is_admin());

drop policy if exists shared_delete_admin on assopilot.shared_state;
create policy shared_delete_admin on assopilot.shared_state
  for delete using (assopilot.is_admin());

-- ───────────────────────────────────────────────────────────
-- 5) DROITS EXPLICITES (filet de sécurité, en plus des default privileges)
--    S'applique aux tables/séquences DÉJÀ créées. La RLS reste la vraie barrière.
-- ───────────────────────────────────────────────────────────
grant usage on schema assopilot to anon, authenticated;
grant select, insert, update, delete on all tables in schema assopilot to authenticated;
grant usage, select on all sequences in schema assopilot to authenticated;

-- ============================================================
--  ENSUITE :
--  1) Exposer le schéma : Settings → API → Exposed schemas → +assopilot
--  2) Te désigner admin (crée le profil membre si absent) :
--        insert into assopilot.members (id, email, role)
--        select id, email, 'admin' from auth.users
--        where email = 'maxime.gerard.be@gmail.com'
--        on conflict (id) do update set role = 'admin';
--  3) Vérifier :  select email, role from assopilot.members;
-- ============================================================
