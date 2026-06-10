# fitai — Design Spec

**Date:** 2026-06-10
**Status:** Approved for planning
**Sibling project:** `../chefai` — fitai reuses chefai's stack, deployment, pure-module
discipline, and i18n. The defining difference is **multi-user accounts**: all data is
scoped to a `user_id` (chefai had no auth and one shared dataset).

## 1. Summary

fitai is a **phone-first, multi-user local web app**, hosted on a DietPi and served on
the home LAN, on port **1313**. Each person on the household LAN creates their own
account; once logged in they stay logged in (long-lived cookie). The app tracks a user's
**fitness state** — body metrics, conditions, goals — and turns it into an LLM-generated,
**adaptive training plan**, with workout-session logging, nutrition logging, and a
plan-centric dashboard with graphs.

fitai is **direct-API-first**: when an Anthropic API key is configured it calls Claude
(Sonnet 4.6) directly to generate/adapt plans and estimate nutrition. A **copy-paste
prompt workflow remains as the graceful fallback** whenever no key is set, the API errors,
or a reply fails to parse. This mirrors chefai's optional direct-inference design, but
makes the direct path the leading UX (fitai is far more interactive — nutrition logging
in particular is painful via copy-paste).

The UI is **French by default** (same i18n structure as chefai, `app/locales/fr.json`),
with a language selector for future locales. Units are **metric** (kg/cm).

## 2. Goals & non-goals

**Goals**
- Per-user accounts with **self-service open registration** (anyone on the LAN can sign up
  from the login page) and cookie-persisted login.
- Track body metrics & daily conditions: weight, steps, body-fat, measurements, energy,
  sleep, soreness — all optional, fast to log.
- Define fitness **goals/objectives** (lose weight, build muscle, endurance, general,
  custom) with target value + timeframe.
- LLM-generated **training plan** from profile + goal + metrics, materialized into planned
  sessions.
- **Adaptive re-planning** driven by logged progress + free-text feedback, with **bounded
  prompt context** (compact long-term summary + a rolling recent window) so cost stays flat
  as history grows.
- **Workout-session logging** (the data that grounds adaptation).
- A **calorie/macro target calculator** (pure, testable) and **nutrition/food logging**
  (manual-first; optional **batched** LLM macro estimation, one call per day).
- A **plan-centric dashboard** with graphs/indicators and a **quick-add FAB** for daily
  stats.

**Non-goals (v1)**
- No social/sharing, no multi-tenant admin/roles (flat list of equal users).
- No wearable / HealthKit / Strava / Google Fit sync (steps are entered manually).
- No progress photos (camera needs a secure context — deferred with the HTTPS upgrade).
- No exercise video/animation library.
- No streaming-to-browser of LLM output (synchronous request + spinner).
- No password reset / email verification (open self-registration only; a user who forgets a
  password is handled out-of-band, e.g. DB edit). Email is not collected.
- No CSRF tokens beyond `samesite=lax` cookies.
- No exact food database / barcode (LLM estimates macros; user can edit).
- No exact inventory of anything; last-write-wins within a single user's own data.

## 3. Architecture

One FastAPI service, server-rendered Jinja2 + HTMX partials + Alpine.js, Tailwind
precompiled at build. Same shape as chefai, plus an **auth layer** and **per-user
scoping**.

```
Browser (phone)
  │  HTML + HTMX partials + Alpine.js (FAB sheet, clipboard, timers) + Chart.js + Tailwind
  ▼
FastAPI ── Jinja2 templates (server-rendered)
  ├── auth            current_user dependency, login/register/logout, session cookie
  ├── nutrition/      PURE: BMR/TDEE → calorie & macro targets
  ├── progress/       PURE: weight trend, goal %, adherence, streak, prompt-context summary
  ├── prompt_builder/ PURE: (profile, goal, metrics_summary, recent_logs, params, lang) → prompt
  ├── response_parser/ PURE: returned/pasted LLM text → validated Pydantic objects
  ├── llm_client      ONLY impure LLM module (Anthropic Sonnet 4.6) — reused from chefai
  ├── routers/        auth, home, metrics, goals, plan, workouts, nutrition, settings
  ├── i18n/           translation catalogs (FR default)
  └── db              SQLite via SQLModel, all rows scoped by user_id
```

### Core invariant — keep the pure modules pure
`nutrition`, `progress`, `prompt_builder`, `response_parser`, and the password helpers in
`security` have **no DB and no web imports**. They hold the real logic and are trivially
unit-testable. `llm_client` is the single module importing the Anthropic SDK. Everything in
`routers/` is thin: auth-scoped CRUD + template rendering + HTMX partial swaps that call
into the pure functions. Do not push business logic into routers or pull DB/SDK access into
the pure modules.

### Deployment
- `Dockerfile` (multi-stage) + `docker-compose.yml`; `uvicorn` serving FastAPI on
  `0.0.0.0:1313`.
- **SQLite on a named volume** (`fitai-data` at `/data`) → data persists across rebuilds
  and reboots.
- Served over plain HTTP on the LAN. HTTPS-PWA is a documented future upgrade (enables
  service-worker offline + camera for progress photos).

## 4. Authentication

The new layer relative to chefai. Two modules keep the testable logic pure:

- **`app/security.py`** (PURE, no DB/web): `hash_password(pw) -> str`,
  `verify_password(pw, hash) -> bool` (bcrypt/argon2 via `passlib` or `pwdlib`), and
  `new_token() -> str` (`secrets.token_urlsafe(32)`).
- **`app/auth.py`**: the `current_user` FastAPI dependency and session helpers.
  - Reads an **opaque random session token** from an `httponly`, `samesite=lax` cookie
    `fitai_session`, looks it up in `UserSession`, returns the `User`.
  - On miss/expiry it raises `NotAuthenticated`; an exception handler registered in
    `main.py` catches it and **303-redirects to `/login`** (for HTML requests).
  - `login(user, response)` creates a `UserSession` row + sets the cookie with a long
    `max_age` (~90 days) → "log in once, stay logged in". `logout` deletes the row + clears
    the cookie.
  - Opaque tokens mean **no signing secret to manage** and support real revocation.

**Routes (no auth required):** `GET/POST /register`, `GET/POST /login`, `POST /logout`.
The `/login` page links to `/register` (open self-registration).

**Isolation:** every data query filters by `current_user.id`. Routers receive the user via
`Depends(current_user)`. Per-user isolation is an explicit test target (user A must never
see user B's rows).

**Security posture (recorded):** passwords hashed (never stored plaintext); cookie
`httponly` + `samesite=lax` (the v1 CSRF mitigation). On plain LAN HTTP the cookie is not
encrypted in transit — acceptable on a trusted home LAN; the HTTPS upgrade path is
documented (§12).

## 5. Data model (SQLite, all user-scoped)

Unless noted, every table below carries a `user_id` foreign key and is filtered by it.

- **User** — `username` (unique), `password_hash`, `created_at`. (No `user_id`; this *is*
  the user.)
- **UserSession** — `user_id`, `token` (unique, indexed), `created_at`, `expires_at`.
  *(Named `UserSession` to avoid clashing with SQLModel's `Session`.)*
- **Profile** (one per user) — `sex`, `birth_date` (→ age for BMR), `height_cm`,
  `activity_level` (sedentary … very active), `language` (default `fr`), `units` (default
  metric); free-text `medical_conditions`, `preferences`, `equipment`; plan defaults
  `days_per_week`, `session_length_min`; `calorie_target_override?`; `use_llm_directly`
  (default `true`).
- **BodyMetric** — `date`, all-optional `weight_kg`, `steps`, `body_fat_pct`,
  `measurements_json` (waist/chest/…), daily condition `energy?` (1–5), `sleep_hours?`,
  `soreness?` (1–5), `notes`. One row = a daily check-in; **only `date` is required**. The
  quick-add FAB writes here (weight, steps, energy).
- **Goal** — `type` (`lose_weight` / `gain_muscle` / `endurance` / `general` / `custom`),
  `target_value?`, `target_date?`, `baseline_value?`, `status` (`active` / `achieved` /
  `abandoned`), `notes`, `created_at`. Multiple allowed; the active one drives generation.
- **TrainingPlan** — `params_json` (days/week, session length, equipment, focus, n_weeks,
  cravings/constraints), `proposals_json` (LLM options stored verbatim until one is chosen),
  `plan_json` (weeks → sessions → exercises), `status` (`proposed` / `active` /
  `superseded` / `cancelled`), `created_at`. Activating one **materializes** PlannedSession
  rows (mirrors chefai's plan → meals).
- **PlannedSession** — `plan_id` FK, `week_index`, `day_index`, `title`, `focus`,
  `exercises_json` (list of `{name, sets, reps, target_weight?, rest?, notes}`),
  `scheduled_date?`.
- **WorkoutLog** — `planned_session_id?` (null = ad-hoc), `date`, `status` (`done` /
  `skipped` / `partial`), `performed_json` (actual sets/reps/weights), `rpe?`, `feeling?`,
  `notes`. **The data that grounds adaptive re-planning.**
- **FoodLog** — `date`, `meal_slot?` (breakfast/lunch/dinner/snack), `description`
  (free text), `calories?`, `protein_g?`, `carbs_g?`, `fat_g?`, `source` (`llm` / `manual`).

Daily nutrition **targets are computed on the fly** by `nutrition.py` from Profile + latest
weight + active Goal (with `calorie_target_override` taking precedence) — **no table**.

**Schema provisioning:** like chefai, the app uses `SQLModel.metadata.create_all` (no
migration tool). `init_db()` also runs an **idempotent column-backfill** so an existing
`fitai.db` gains columns added in later versions (chefai's `_ensure_*_columns` pattern).

## 6. Pure modules

- **`nutrition.py`** — `compute_targets(profile, latest_weight_kg, goal) -> Targets`.
  BMR via **Mifflin–St Jeor** (sex/age/height/weight), TDEE = BMR × activity multiplier,
  goal-adjusted calories (deficit for `lose_weight`, surplus for `gain_muscle`, maintenance
  otherwise), protein target (g/kg bodyweight), carb/fat split. `calorie_target_override`
  short-circuits to a manual target. The "calorie/macro calculator" — the `decrement.py` of
  fitai.
- **`progress.py`** — pure summaries over a user's logs:
  - **Dashboard indicators:** weight trend (7-day moving average + Δ), goal-progress %,
    adherence (sessions done ÷ planned over the active plan), current streak.
  - **Prompt-context compression (§7):** `build_context_summary(metrics, logs, goal)`
    produces a *compact* long-term summary (current weight + Δ over 4/12 weeks,
    goal-progress %, adherence ratio, notable recent lifts/PRs) — the bounded input to
    adaptation prompts, independent of how long the user has tracked.
- **`prompt_builder.py`** — pure `(profile, goal, metrics_summary, recent_logs, params,
  lang) -> prompt`. Each flow has a **JSON variant** (direct API) and a **prose variant**
  (copy-paste fallback). Flows: generate plan, adapt/re-plan, estimate nutrition. Re-roll
  appends a "ne propose pas à nouveau: X, Y" clause from an optional `exclude` list (stays
  stateless; titles ride on the request).
- **`response_parser.py`** — lenient fenced-JSON extraction (locate the JSON block within
  surrounding prose) → Pydantic for: plan, adapted plan, and a **batched** nutrition list
  (`parse_nutrition_list_response` → one estimate per submitted food). On failure: a
  clear French message + re-paste box. **Never half-saves** (transactional).
- **`security.py`** — password hash/verify + token generation (see §4).

## 7. LLM flows & context compression

All LLM access goes through **`llm_client.py`** (reused from chefai): Anthropic **Sonnet
4.6** (`FITAI_LLM_MODEL` override), streaming internally
(`messages.stream(...).get_final_message()`) so long plans don't hit HTTP timeouts,
adaptive thinking, `max_tokens ≈ 8000`, raising a typed `LLMError`. Pure
`prompt_builder` → `llm_client.complete()` → pure `response_parser`. The API path and the
copy-paste path share one parsing path.

| Flow | Direct-API path (default) | Copy-paste fallback |
|---|---|---|
| **Generate plan** (`/plan/generate`) | build context → `complete()` → `parse_plan_response` → store proposals → render proposal cards; **re-roll** ("autre programme") | render prose prompt; user pastes JSON back → same parser |
| **Activate plan** | chosen proposal → materialize PlannedSession rows | identical (post-parse) |
| **Adapt plan** (`/plan/adapt`) | inject `progress.build_context_summary` + free-text feedback → `complete()` → parse adapted plan → supersede old, materialize new | prose prompt; paste back |
| **Estimate nutrition** (`/nutrition/estimate`) | **manual-first, batched**: macros are typed by default (0 calls); one explicit "Estimer les repas du jour" button sends all un-estimated foods for the day in a **single** `complete()` call → `parse_nutrition_list_response` → pre-fill each FoodLog row (editable before save) | prose prompt; paste back, or log manually |

### LLM call points & cost control

The API is called at **exactly three explicit user actions** — never on data entry or
viewing:

1. **Generate plan** (`/plan/generate`), plus the **re-roll** button (1 call each).
2. **Adapt plan** (`/plan/adapt`).
3. **Estimate nutrition** (`/nutrition/estimate`) — opt-in, **batched** (one call for all
   un-estimated foods of the day), **manual entry needs no call**.

Everything else is **0 API calls**: adding weight/steps/energy (FAB), logging a workout,
editing goals, the dashboard, all trend graphs, and the **calorie/macro target calculator**
(`nutrition.py`, deterministic math).

**Workout-session feedback is free at capture.** When you log a session — `status`, `rpe`,
`feeling`, and free-text `notes` (e.g. *"le genou tire"*, *"trop facile"*) — it is **only
stored** in `WorkoutLog`; no call fires. That accumulated feedback is read later by
`progress.build_context_summary` + the recent-window logs and folded into the **next
`/plan/adapt` call**, so a week of session feedback costs **one** call when you choose to
adapt — not one per session. The whole direct path is **hard-gated** —
`ANTHROPIC_API_KEY` set *and* `use_llm_directly` on — otherwise every flow falls back to the
zero-cost copy-paste path. Expected steady-state volume is low: ~1 plan-gen + ~1 adapt per
week, plus at most one batched nutrition call per day for users who opt in.

**Context compression (the answer to "do we need it for long-term tracking?"):** Yes.
Adaptation/generation prompts are **bounded** = *compact long-term summary*
(`progress.build_context_summary`) **+** a *rolling raw window* of only the **last ~7–14
days** of workout/nutrition/weight logs **+** the user's free-text feedback. Token cost
stays flat whether the user has tracked for one week or two years. This keeps
`prompt_builder` pure (it receives the already-summarized context, it does not query the DB).

**Fallback behavior:** any failure — not configured, `LLMError`, or `ParseError` — renders
the copy-paste prompt partial **plus a short French note** (e.g. *"Génération directe
indisponible — copiez le prompt ci-dessous."*). Storage stays transactional.

## 8. UI / design language

**Direction: "Daylight + violet"** (validated via visual companion).

- **Base:** light — `#f5f7fa` page, white `rounded-2xl` cards, soft shadows, generous
  spacing, subtle transitions. Phone-first.
- **Violet identity:** primary gradient `#6d5efc → #8b7bff` on CTAs, the FAB, active nav,
  progress rings, sparklines, and progress bars; deep `#5b4bd6` for text accents; avatar
  chip `#e7e1ff`.
- **Hero session card:** dark indigo-violet gradient (`#1b1733 → #2c2156`) so the active
  plan's "Séance du jour" pops against the light page.
- **Semantic colors retained:** red (`#e0556b`) for weight-down / alerts, etc.
- Implemented as the **Tailwind theme** (precompiled at build, Tailwind **v3.4.17** pin —
  v4 drops the color utilities, per chefai's lesson).
- **Charts:** **Chart.js vendored at build** (CDN-free, like htmx/alpine) for weight / steps
  / calorie trend lines and goal-progress rings; small **inline-SVG sparklines** for compact
  dashboard tiles.

### Navigation (French, bottom tab bar)
Header shows the logged-in **username + logout (⎋)** and a ⚙️ link to Réglages.
Bottom tabs: **Accueil · Suivi · Programme · Nutrition · Réglages**.
A **floating "+" FAB** (bottom-right, above the tab bar) is persistent across tabs.

- **Accueil (plan-centric dashboard)** — leads with the **"Séance du jour" hero card**
  (today's session from the active plan; tap → log/start it), then a **week strip** (this
  week's planned sessions: done ✓ / today / upcoming), then **stat tiles**: Poids
  (sparkline + Δ), Pas (ring), Calories (bar vs target + macros), Objectif (ring). The
  active plan is the centerpiece of the app.
- **Suivi** — **Objectifs** section (goals) on top; body-metric daily check-in + history /
  trend graphs (weight, steps, body-fat).
- **Programme** — the active plan, this week's sessions, **log a workout**, generate /
  adapt buttons; plan proposals → activate.
- **Nutrition** — today's food log + running totals vs target; quick add with LLM estimate.
- **Réglages** — profile (sex, birth date, height, activity), equipment, days/week,
  language, LLM direct-mode toggle, logout.
- **Quick-add FAB** — opens an Alpine-driven bottom sheet to log **daily stats — weight,
  steps, energy** in two taps (writes a `BodyMetric` row), with a shortcut to quick
  food-log.

## 9. App structure

```
app/
  main.py            FastAPI app, startup (init_db + seed defaults), router auto-registration,
                     NotAuthenticated → /login exception handler
  config.py          REPO_ROOT, DB_PATH (FITAI_DB_PATH env), APP_TITLE
  db.py              SQLite engine + init (+ idempotent column backfill, chefai pattern)
  models.py          User, UserSession, Profile, BodyMetric, Goal, TrainingPlan,
                     PlannedSession, WorkoutLog, FoodLog
  schemas.py         Pydantic for parsed LLM replies (plan, adapted plan, nutrition estimate)
  enums.py           activity levels, goal types, meal slots, exercise focus, units
  security.py        PURE: hash/verify password, token generation
  auth.py            current_user dependency, login/register/session helpers
  nutrition.py       PURE: BMR/TDEE → calorie & macro targets
  progress.py        PURE: trends, adherence, streak, prompt-context summary
  prompt_builder.py  PURE: prompt text (JSON + prose variants)
  response_parser.py PURE: returned/pasted LLM text → validated objects
  llm_client.py      ONLY impure LLM module (Anthropic Sonnet 4.6) — reused from chefai
  i18n.py            t() translation lookup, registered as a Jinja global
  seed.py            seeds per-user Profile on registration; default enums
  routers/           auth, home, metrics, goals, plan, workouts, nutrition, settings
  templates/         Jinja2; partials/ are HTMX swap fragments (leading _)
  static/            css (Tailwind), js/app.js, vendor/ (htmx, alpine, chart.js), manifest
  locales/           fr.json
```

## 10. Error handling

- **LLM parse / API failure:** fall back to the copy-paste prompt partial + a short French
  note; never half-save (transactional), per §7.
- **Paste-back parsing:** lenient JSON extraction → Pydantic validation → on failure a clear
  French message with a re-paste box.
- **All metric/condition fields optional** — the only required field on a daily check-in is
  the date; the only required field on a food log is the description.
- **Auth:** invalid login → re-render `/login` with a French error; duplicate username on
  register → French error; unauthenticated access to a protected route → 303 → `/login`.
- **Plan activate / cancel** are explicit; adapting supersedes (the old plan is retained as
  `superseded`, not destroyed).

## 11. Testing (TDD)

- **Pure unit:**
  - `nutrition` — BMR/TDEE/targets across sex, age, activity level, and each goal type;
    override short-circuit.
  - `progress` — weight moving-average + Δ, goal-progress %, adherence ratio, streak, and
    `build_context_summary` bounding (long history → fixed-size summary + recent window).
  - `prompt_builder` — each flow injects profile + goal + metrics summary + constraints; the
    `exclude` re-roll clause; JSON vs prose variants.
  - `response_parser` — well-formed and malformed plan / adapted-plan / nutrition JSON;
    fenced-block extraction from surrounding prose.
  - `security` — hash/verify roundtrip, wrong-password rejection, token uniqueness.
- **Integration (FastAPI `TestClient`, `llm_client.complete` mocked — no real network):**
  - Auth: register → login → cookie set → access a protected route → logout → access denied.
  - **Per-user isolation:** user A cannot read/modify user B's metrics, goals, plans, logs.
  - Plan: generate (mocked) → store proposals → activate → PlannedSession rows materialized.
  - Workout log: log a planned session → adherence reflects it.
  - Nutrition: estimate (mocked) → editable pre-fill → save FoodLog → totals vs target.
  - Fallback: `LLMError` and `ParseError` both fall back to the copy-paste prompt partial.
  - **No-call assertion (cost):** posting a BodyMetric (weight/steps/energy), a WorkoutLog
    (incl. free-text feedback), a goal, or a manual FoodLog must **not** invoke
    `llm_client.complete` — asserted with a spy/mock that records zero calls.
- **Fixtures:** a seeded user with profile/goal/metrics; sample LLM responses as test data
  files (plan, adapted plan, nutrition estimate).

## 12. CI/CD & documentation

- **GitHub Actions CI** (`.github/workflows/build.yml`, chefai's pattern):
  - Triggers on push to default branch, version tags, and PRs.
  - Lints + runs the pytest suite (unit + integration).
  - Builds the Docker image with `buildx`/QEMU for **multi-arch** (`linux/amd64`,
    `linux/arm64` — `arm/v7` omitted, no uvloop/httptools wheels) so it runs on a DietPi and
    on x86.
  - Publishes to **GHCR** (`ghcr.io/<owner>/fitai`), tagged `latest` + git SHA / version.
- **README.md** with: what fitai is + the accounts model in one paragraph; quick start
  (`docker compose up -d`, the GHCR image, env/port/volume config); a **DietPi LAN
  walkthrough** (pull multi-arch image, persistent volume for SQLite, find LAN address, open
  on phone, add-to-home-screen); **SQLite backup/restore**; and the **HTTPS-PWA upgrade
  path** (enables service-worker offline + camera for progress photos) as an optional
  advanced section.
- **Config / secrets:** `ANTHROPIC_API_KEY` via env (standard SDK resolution, injected
  through docker-compose, **never stored in SQLite** — matches the `.env` rule);
  `FITAI_LLM_MODEL` (default `claude-sonnet-4-6`); `FITAI_DB_PATH` (default
  `/data/fitai.db`); port `1313`.

## 13. Tech stack

- **Backend:** Python 3.11+, FastAPI, SQLModel (SQLite), `passlib`/`pwdlib` for password
  hashing, `anthropic` SDK.
- **Frontend:** Jinja2 server-rendered, HTMX for partial updates, Alpine.js (FAB sheet,
  clipboard/paste, timers, awake-screen during workouts), Chart.js (vendored), Tailwind
  (precompiled, v3.4.17 pin).
- **Packaging:** Docker + docker-compose, SQLite on a persistent named volume.
- **PWA:** manifest + add-to-home-screen; full offline (service worker) deferred to an HTTPS
  deployment.

## 14. Deferred / follow-on features

- **HTTPS deployment** → unlocks service-worker offline + **progress photos** (camera needs
  a secure context) + reliable PWA.
- **Wearable / health-platform sync** (Strava, Google Fit, Apple Health) for auto steps /
  workouts / heart rate.
- **Exercise library** with form cues, alternatives/swaps, demo media.
- **Personal-record (PR) tracking & charts**, per-exercise progression graphs.
- **Password reset / email**, account settings (rename, change password, delete account).
- **Per-request model selection, streaming-to-browser, usage/cost dashboard.**
- **Recipe/meal integration with chefai** (shared nutrition vocabulary) — possible later.
- **Reminders / notifications** (e.g. "séance du jour"), requires PWA push (HTTPS).
