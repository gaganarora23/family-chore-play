# Design System

Minimal, server-rendered-templates-first conventions for the MVP's ~4-5
screens (`_docs/plan.md` §19). Keep this in sync with what's actually
built -- it documents real conventions, not aspirational ones.

## Principles

- Plain HTML + Django templates + HTMX partial swaps. No SPA framework,
  no client-side state beyond what HTMX needs for a swap.
- Mobile-first: family members will use this from a phone as often as a
  parent uses it from a laptop.
- Legible at a glance -- the dashboard's job is to answer "what's left
  today?" in one screen, not to be dense with data.

## Roles, visually

Two roles see different chrome, not different color themes:

- **Parent** views get an extra top-level nav item ("Manage Chores",
  "Approvals") and management controls (edit/create buttons) that family
  members never see, rather than the same page with hidden buttons.
- **Family member** views are read-mostly plus the two actions they can
  take: Claim and Mark Done.

## Shared components

- **Chore row/card** -- name, point value, and a status-dependent action
  or badge:
  - `available` (claimable): "+N points" + a `Claim` button.
  - `assigned`/`claimed`, incomplete: a `Mark Done` button.
  - `pending_approval`: a "waiting for approval" badge, no action.
  - `completed`: a checkmark, muted/de-emphasized.
  - `missed`: a muted row in history views, not shown on the live
    dashboard.
- **Streak badge** -- 🔥 + current streak count, shown next to a chore
  row when a `StreakRecord` for it has a non-zero streak (plan §13).
- **Points total** -- family member name + running total, used both on
  the dashboard's points summary and reward-progress sections.
- **Reward progress** -- reward name + a progress indicator (bar or
  "X / N points") toward its threshold.
- **Approval queue row** -- family member name, chore name, an `Approve`
  button; parent-only.

## Interaction pattern

Claim, Mark Done, and Approve are all `POST` + HTMX swap of the single
affected row/card -- no full page reload, no client-side framework state
(see `_docs/api.md`). Use a brief, obvious success state (e.g. the row
transitioning to its next status) rather than a separate confirmation
dialog.

## Not yet decided

- Exact color palette / typography -- to be picked when the first screen
  is actually built, not in the abstract.
- Whether children get a simplified/larger-touch-target variant of the
  family-member view.
