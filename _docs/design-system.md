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

- **Chore row/card** (`chores/_chore_row.html`) -- name, point value, and
  a status-dependent action or badge:
  - `available` (claimable, unclaimed): "+N points" + a green `Claim`
    button.
  - `available`/`claimed`, already the viewer's (assigned, or claimed by
    them): a green `Mark Done` button.
  - `pending_approval`: an amber "Waiting for approval" pill, no action.
  - `completed`: a green "✓ Done" pill.
  - `missed`: a muted gray "Missed" pill.
- **Streak badge** -- 🔥 +N, shown next to a chore row when a
  `StreakRecord` for it has a non-zero streak (plan §13). Rendered from an
  attribute the view annotates onto the instance (`current_streak`), not
  a template lookup -- see `home()`.
- **Points total** -- family member name + running total, used both on
  the dashboard's points summary and reward-progress sections. Shows the
  member's username (`user.get_username`), not `FamilyMember.__str__()`
  (which is verbose -- meant for admin/debug, not end-user UI).
- **Reward progress** -- reward name + "X / N points" and/or "X / N
  streak" toward its thresholds, with a "✓ Unlocked" pill once met.
- **Approval queue row** -- family member name, chore name, an `Approve`
  button; parent-only. Lives in a table, not the shared chore-row
  component (see "Tables vs. cards" below).

## Interaction pattern

Claim and Mark Done are `POST` + HTMX swap of the single affected
row/card (`hx-post` + `hx-target` + `hx-swap="outerHTML"` on the row's
own `<li>`, CSRF sent via `hx-headers` inherited from that same element)
-- no full page reload, no client-side framework state (see
`_docs/api.md`). The swapped-in row is just the `_chore_row.html`
fragment re-rendered with the instance's new status, which gives the
"row transitions to its next state" success feedback for free.

**Approve is a plain form POST (full page reload), not HTMX**, unlike
Claim/Mark Done. The approval queue is a table (member + chore + points +
action, one row per pending instance) rather than the chore-row card
list, since it needs a "who" column the shared component doesn't have --
swapping a `<tr>` for an `_chore_row.html` `<li>` fragment would be
invalid markup. If the approval queue ever grows real-time needs, revisit
by either giving it its own row partial or dropping the table for a
card list.

## Tables vs. cards

- The live dashboard's chore feed (Today / Available to Claim) is a card
  list (`.chore-list` of `.chore-row`s) -- it's the frequently-glanced-at,
  interactive surface.
- Management/list pages a parent visits deliberately -- Chores, Rewards,
  Approvals -- are plain tables (wrapped in `.table-wrap` for horizontal
  scroll at phone width) since the data is inherently tabular (several
  columns) and these pages aren't optimized for one-thumb scanning the
  way the dashboard is.

## Color palette & typography

Picked when the first real screens landed (dashboard, forms, tables);
green as the primary/brand color, per product request. Defined as CSS
custom properties in `chores/static/chores/style.css`, consumed by every
template via `chores/templates/chores/base.html`:

- `--color-primary` (`#2f9e44`) / `--color-primary-dark` (`#22803a`) --
  buttons, links, the brand mark, positive badges (completed, unlocked).
- `--color-primary-light` (`#e9f7ee`) -- tinted backgrounds for positive
  badges and row hover states.
- `--color-amber` / `--color-amber-bg` -- the "pending approval" badge
  only; nothing else uses amber.
- `--color-bg` (`#f6f8f6`) / `--color-surface` (`#fff`) / `--color-border`
  (`#e1e8e3`) / `--color-text` / `--color-text-muted` -- neutral page
  chrome, cards, and tables.
- Typography: system font stack (`-apple-system, ... sans-serif`), no
  webfont -- keeps it fast and avoids an external font request.
- Spacing/radius: a small custom-property scale (`--space-1`...
  `--space-6`, `--radius`, `--radius-sm`) rather than a utility framework
  like Tailwind, to keep the stylesheet dependency-free per the "no SPA
  framework" principle.

## Base template & static assets

Every template extends `chores/templates/chores/base.html`, which owns
the `<head>` (viewport meta, `style.css` link, the HTMX `<script>` tag
loaded only for authenticated pages) and the site header/nav. Pages fill
in `{% block title %}` and `{% block content %}` only. The nav is
role-aware via a `current_family_member` template variable injected by
`chores.context_processors.family_member` (registered in
`TEMPLATES.OPTIONS.context_processors`) -- a parent sees Chores /
Approvals / Rewards links a family member doesn't, per "Roles, visually"
above, without every view needing to look up and pass the role itself.

## Not yet decided

- Whether children get a simplified/larger-touch-target variant of the
  family-member view.
