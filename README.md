# family-chore-play

A shared household chore manager. See `_docs/plan.md` for the product plan
and `_docs/architecture.md` for the technical approach.

## Setup

Requires a PostgreSQL database reachable with the settings in
`.env.example` (copy it to `.env`, or export the same variables another
way).

```sh
uv sync
uv run manage.py migrate
uv run manage.py runserver
```

## Tests

```sh
uv run pytest
```

See `AGENTS.md` for the full set of commands and `_docs/testing-guidelines.md`
before adding new tests.

## Endpoints

| Method | URL | View | Who |
|---|---|---|---|
| GET | `/` | `home` | any logged-in user (dashboard: today's chores, available pool, streaks, reward progress, points summary) |
| GET/POST | `/login/` | Django `LoginView` | anyone |
| POST | `/logout/` | Django `LogoutView` | logged-in |
| GET | `/admin/` | Django admin | staff/superuser |
| GET/POST | `/chores/new/` | `chore_create` | parent |
| GET | `/chores/new/success/` | `chore_create_success` | parent |
| GET | `/chores/` | `chore_list` | parent (own household) |
| GET/POST | `/chores/<pk>/edit/` | `chore_edit` | parent (own household's chore) |
| POST | `/instances/<pk>/claim/` | `claim_chore` | family member -- returns an HTML fragment |
| POST | `/instances/<pk>/done/` | `mark_chore_done` | the instance's `claimed_by` -- fragment |
| GET | `/approvals/` | `approval_queue` | parent (own household) |
| POST | `/instances/<pk>/approve/` | `approve_completion` | parent (own household) -- fragment |
| GET | `/rewards/` | `reward_list` | parent (own household) |
| GET/POST | `/rewards/new/` | `reward_create` | parent |

Everything except `/login/` and `/admin/` requires being logged in; parent-only
routes 403 for a family member and redirect anonymous users to `/login/`. The
three POST-only fragment endpoints (`claim`, `done`, `approve`) are meant to be
called from a chore row via HTMX, not visited directly -- a bare GET returns
405.
