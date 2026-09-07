# Shared Household Chore Manager --- Architecture

## 1. Purpose

This document describes the chosen technology stack and high-level
architecture for building the MVP described in `_docs/plan.md`. It
covers the framework, data model, and how the plan's key rules (claiming,
approval, recurrence, streaks) map onto the stack.

## 2. Chosen Stack: Django + PostgreSQL

**Stack:** Django (Python), PostgreSQL, deployed on a PaaS such as
Render, Fly.io, or Railway.

**Frontend approach:** Server-rendered Django templates, with HTMX (and
a little Alpine.js where needed) layered in for the interactions that
benefit from partial-page updates without a full reload --- claiming a
chore, marking a chore done, and approving a completion. This avoids
standing up a separate frontend build pipeline or a JSON API for the
MVP's ~4-5 screens.

**Why this fits the plan:**

- The plan describes a small set of CRUD entities (chores, family
  members, assignments/claims, completions) with role-based permissions
  (parent vs. family member) --- exactly what Django's ORM, admin, and
  auth system are built for.
- Django's built-in **auth system** covers login/session handling, and
  its **admin panel** gives a working parent-facing chore/point
  management UI almost for free, which can double as (or bootstrap) the
  real parent UI described in the plan.
- The rules in the plan --- first-to-claim, per-chore verification mode,
  recurrence expansion, streak/missed-chore tracking --- are all
  server-side business logic best expressed as model methods and
  transactions, not client-side state. A traditional server-rendered
  app keeps this logic in one place.
- Low traffic, single-household scale means Django's "batteries
  included" defaults (no need for a separate API layer, background job
  queue, or SPA state management) minimize infrastructure decisions.

**Trade-offs accepted:**

- If a native mobile app or a richer, more app-like frontend is wanted
  later, a JSON API layer (Django REST Framework) would need to be
  added alongside or instead of the template-rendered views.
- HTMX-driven interactivity is less flexible than a full SPA framework
  for complex client-side state, but the plan's screens don't require
  that (per plan section 19: a handful of simple, mostly server-driven
  screens).

## 3. High-Level Components

```
Browser (HTML + HTMX)
        |
        v
Django views (server-rendered templates)
        |
        v
Django models / ORM  ---  business rules (claiming, approval,
        |                  recurrence, streaks)
        v
PostgreSQL
```

- **Django views**: one set of views per role-relevant screen (parent
  dashboard, family member dashboard, chore creation/edit, approval
  queue). Permissions enforced via Django's auth + simple role checks
  (parent vs. family member).
- **Models**: the primary source of truth for chore state and history
  (see Section 4). Business rules that must be atomic --- most notably
  claiming --- are implemented as model/service methods wrapped in a
  database transaction with a uniqueness constraint, so two family
  members cannot both claim the same chore.
- **Background/scheduled task**: a daily job (Django management command
  run via cron, or `django-crontab`/Celery beat if needed) that expands
  recurring chore definitions into that day's chore instances and marks
  yesterday's incomplete instances as **Missed**.

## 4. Data Model (Sketch)

This is a starting sketch, not a final schema:

- **Household**: groups a set of users together. (Even for a
  single-family MVP, scoping data by household from day one keeps the
  door open to more than one family later without a rewrite.)
- **User / FamilyMember**: extends Django's user model with a `role`
  (parent or family member) and a household link.
- **ChoreDefinition**: the template for a chore --- name, point value,
  ownership type (assigned vs. claimable), assigned member (if
  applicable), recurrence rule, verification mode (instant vs. parent
  approval).
- **ChoreInstance**: a specific day's occurrence of a chore definition
  (or a one-off chore), with its own status: available, claimed,
  pending approval, completed, missed. This is the row that claiming,
  completion, and approval actions operate on.
- **Completion**: records who completed a `ChoreInstance` and when,
  linked to the points awarded.
- **StreakRecord**: tracks the current and best streak per family
  member per chore definition, updated on completion/miss.
- **Reward**: describes a reward and its point/streak threshold;
  progress is derived from points/streaks rather than duplicated state
  where possible.

Keeping `ChoreDefinition` (the recurring template) separate from
`ChoreInstance` (a specific day's actual chore) directly supports the
plan's requirements around recurrence, missed-chore history, and
streaks without ambiguity about "which day" a given claim or completion
refers to.

## 5. Key Rules Mapped to Implementation

| Plan rule | Implementation approach |
|---|---|
| First-to-claim, no unclaiming (§7) | Claim action wrapped in a DB transaction with a status check on `ChoreInstance` (`available` → `claimed`), preventing double-claims under concurrent requests. |
| Instant vs. parent-approval completion (§8) | `ChoreDefinition.verification_mode` branches the "mark done" action: instant completion updates status + awards points immediately; approval mode sets status to `pending_approval`, visible in a parent approval queue view. |
| Recurring chores (§10) | Daily scheduled job expands each active `ChoreDefinition`'s recurrence rule into today's `ChoreInstance`, if one doesn't already exist. |
| Missed chores (§12) | Same daily job marks any prior day's `available`/`claimed` `ChoreInstance` as `missed` if not completed, and breaks the associated `StreakRecord`. |
| Streaks (§13) | `StreakRecord` incremented on completion of a scheduled instance, reset on a `missed` instance, computed by the daily job and/or on completion. |
| Rewards (§14) | Reward progress computed from a family member's point total and relevant `StreakRecord`s; no separate ledger needed for the MVP. |

## 6. Deployment

- **App**: Django app deployed to a small PaaS instance (Render, Fly.io,
  or Railway all support Django + Postgres with minimal config).
- **Database**: managed PostgreSQL instance from the same provider.
- **Scheduled job**: platform-native cron (e.g., Render Cron Jobs) or
  `django-crontab` running the daily recurrence/missed-chore job.
- **Static assets**: served via WhiteNoise or the platform's static
  file handling --- no CDN or separate asset pipeline needed at this
  scale.

## 7. Open Questions to Resolve Before Implementation

- **Login experience for kids**: a shared household PIN, individual
  simple passwords, or parent-managed profile switching? This shapes
  the auth views more than anything else in this document.
- **Multi-household support**: the `Household` model above assumes it
  from day one at low cost --- confirm this is desired versus a
  single-household simplification.
- **Timezone handling for "Today"**: since the plan explicitly avoids
  specific times (§11) but still needs a daily rollover for
  recurrence/missed-chore logic, the household's local timezone needs
  to be defined somewhere (e.g., on the `Household` model).

## 8. Next Step

Per plan §19, define the ~4-5 core screens (parent dashboard, family
member dashboard, chore creation/edit, approval queue, and possibly a
rewards/history view) and their navigation before writing any code.
