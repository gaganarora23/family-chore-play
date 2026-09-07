# Shared Household Chore Manager --- Tech Stack Options

## 1. Purpose

This document proposes candidate technology stacks for building the MVP
described in `_docs/plan.md`. No implementation decisions are made here
--- the goal is to lay out realistic options with their trade-offs so a
stack can be chosen deliberately.

## 2. What the Stack Needs to Support

Before comparing options, it's worth naming the actual requirements the
plan implies, since these are what should drive the choice:

- **A responsive website**, not a native app. No offline/native
  requirements.
- **Two user roles** (parent, family member) with different
  permissions, and a lightweight, family-friendly login (kids won't
  manage a "real" password easily --- PIN-style or simple auth is
  common in this space).
- **A relational-ish data model**: households, users, chores,
  assignments/claims, completions, points, streaks, rewards. Lots of
  "who owns what, as of when" state and history (missed chores,
  streak history).
- **Server-side logic with rules**: first-to-claim races, approval
  workflows, recurrence expansion, streak calculation. This benefits
  from a real backend rather than pure client-side logic.
- **Low traffic, low scale**: this is a household tool, not a
  multi-tenant SaaS at launch. Scale is not a real constraint; developer
  speed and low operating cost are.
- **A dashboard-first UI** with a handful of screens (per plan section
  19: ~4-5 screens) --- not a complex SPA with heavy client state.

These point toward "boring, well-trodden, fast to build" more than
"scalable" or "cutting edge."

## 3. Stack Options

### Option A: Full-Stack JS/TS Framework (Next.js + Postgres)

**Stack:** Next.js (React) for frontend + backend API routes, Prisma
ORM, Postgres (e.g. hosted on Supabase, Neon, or Railway), NextAuth or
a simple custom session/PIN auth, deployed on Vercel.

**Why it fits:** One language (TypeScript) across the whole app, one
repo, one deploy. Next.js's server actions/API routes are a natural
place to put chore-claiming and approval logic transactionally.
Postgres models the relational data (households → members → chores →
completions) cleanly, including history for streaks/missed chores.
Huge ecosystem, so libraries exist for everything (calendars/recurrence
helpers, form handling, etc.).

**Trade-offs:** More moving pieces than a monolith framework
(Prisma + Postgres + auth library + hosting all separate concerns to
wire up), though each piece is well-documented. Slight overkill if the
household app never needs to scale beyond a few users, but the extra
structure pays off if the project grows past the MVP.

**Best if:** You want a modern, resume-friendly, TypeScript-everywhere
stack and don't mind a bit of setup ceremony up front.

---

### Option B: "Batteries-Included" Framework (Ruby on Rails or Django)

**Stack:** Rails (with Hotwire/Turbo for interactivity) or Django (with
HTMX), Postgres or SQLite, built-in auth (Devise for Rails / Django's
auth system), deployed on Render, Fly.io, or Heroku-style PaaS.

**Why it fits:** These frameworks are optimized for exactly this shape
of app: server-rendered CRUD with roles, relationships, and background
rules --- a to-do/points/approval system is squarely in their wheelhouse.
Convention-over-configuration means less time deciding "how do we
structure this" and more time building features. Hotwire/HTMX let you
get dashboard-style live updates (e.g., a chore disappearing from the
"available" pool when claimed) without writing a separate frontend
SPA or API layer.

**Trade-offs:** Less trendy than a JS SPA stack; if the long-term plan
includes a native mobile app later, you'd eventually add a separate
API layer. Team/personal familiarity with Ruby or Python matters more
here than with JS if this is a solo hobby project and JS is already
your daily language.

**Best if:** You want the fastest path to a working, server-rendered
MVP with minimal architectural decisions, and you're comfortable in
Ruby or Python.

---

### Option C: Lightweight/Serverless (SvelteKit or Remix + Managed BaaS)

**Stack:** SvelteKit or Remix for the frontend + light backend routes,
paired with a managed backend-as-a-service like Supabase (Postgres +
auth + realtime) or Firebase (Firestore + auth).

**Why it fits:** Minimizes backend code you have to write yourself ---
auth, database, and even realtime "chore claimed" updates come mostly
for free from the BaaS. Fast to prototype the 4-5 screens from the
plan. Supabase in particular gives you a real Postgres database (good
for the relational chore/points model) plus row-level security, which
maps naturally onto "parents can do X, family members can do Y."

**Trade-offs:** Some business logic (claim races, approval flow,
recurrence/streak calculation) is awkward to express purely through a
BaaS's rules engine and often ends up in a serverless function anyway,
partially eroding the "no backend" benefit. Firebase's NoSQL model fits
this relational data less naturally than Supabase's Postgres does.

**Best if:** You want to move fast and are comfortable delegating
auth/infra to a managed service, accepting some lock-in to that
provider.

---

### Option D: Minimal Custom Stack (Flask/Express + SQLite)

**Stack:** A small Flask (Python) or Express (Node) app, server-rendered
templates (Jinja2 / EJS) or a thin client-side JS layer, SQLite as the
database, deployed on a single small VM or PaaS (Fly.io, Render).

**Why it fits:** Nothing here is more than what's needed for a
household-scale app used by a handful of people. SQLite is more than
sufficient for this data volume and removes a whole category of
"managing a database service" concerns. Every piece is simple enough
to fully understand and debug, which matters for a side project you
maintain solo.

**Trade-offs:** You write more plumbing by hand (auth, sessions, role
checks) than with Option A or B's built-ins. SQLite makes concurrent
writes across many households a future concern if this ever grows
beyond one family --- easy to migrate later, but worth naming now.

**Best if:** You want the simplest possible thing that works, full
visibility into every layer, and minimal external dependencies or
accounts.

## 4. Comparison at a Glance

| Option | Language | DB | Auth | Ops Complexity | Best for |
|---|---|---|---|---|---|
| A: Next.js + Postgres | TypeScript | Postgres | NextAuth/custom | Medium | Modern TS stack, room to grow |
| B: Rails/Django | Ruby/Python | Postgres/SQLite | Built-in | Low-Medium | Fastest CRUD+roles MVP |
| C: SvelteKit/Remix + Supabase | TypeScript | Postgres (managed) | Managed | Low | Speed via managed backend |
| D: Flask/Express + SQLite | Python/JS | SQLite | Custom | Very Low | Simplest, fully self-contained |

## 5. Open Questions to Resolve Before Choosing

- Is this a single household, or should the data model support
  multiple households from day one (multi-tenancy)? All four options
  can support this, but it affects how much auth/isolation work is
  needed up front.
- How important is "resume/learning value" of the stack vs. pure
  speed to a working MVP?
- Is there an existing hosting account/preference (Vercel, Fly.io,
  Render, etc.) that should narrow these options?
- What login experience is wanted for kids --- a shared household PIN,
  individual simple passwords, or parent-managed profile switching
  (like Netflix profiles)? This affects the auth approach more than
  the framework choice.

## 6. Recommendation

Given the plan's emphasis on a small, simple, MVP-scoped website with a
handful of screens and moderate server-side logic (claiming races,
approvals, recurrence, streaks), **Option B (Rails or Django)** or
**Option D (Flask/Express + SQLite)** best match the actual scope ---
they minimize architecture decisions and get to a working end-to-end
loop fastest. **Option A (Next.js + Postgres)** is the better choice if
TypeScript end-to-end is a strong preference or future growth (more
users, a public launch) is anticipated. Final choice should follow from
the open questions above rather than technology preference alone.
