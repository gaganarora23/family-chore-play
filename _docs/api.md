# API

## No JSON/REST API in the MVP

`_docs/architecture.md` (§2) deliberately chose server-rendered Django
templates plus HTMX over a JSON API + frontend split, because the plan's
~4-5 screens don't need one. **Do not add Django REST Framework, DRF
serializers, or a `/api/` namespace for MVP tasks.** If a task seems to
need one, stop and ask rather than introducing an API layer.

What follows instead is a map of the **HTMX endpoints** each Django view
exposes -- the closest thing this app has to an API surface, and what an
agent building or calling a view needs to agree on.

## Conventions

- Every endpoint is a normal Django view returning either a full page
  (`GET` navigations) or an HTML fragment (`HX-Request` requests, used for
  partial updates -- claim, mark done, approve).
- Fragment responses re-render just the affected piece of the page (a
  single chore row/card, a dashboard section), not the whole page.
- Role checks (parent vs. family member) are enforced server-side in the
  view, the same as full-page views -- never assume the client hid a
  button correctly.
- State-changing endpoints are `POST`-only and re-check the object's
  current status inside the transaction (see the claim rule below) rather
  than trusting what the client last rendered.

## Endpoints by feature (fill in as each task lands)

| Action | Method | URL (indicative) | Returns | Role |
|---|---|---|---|---|
| Dashboard | `GET` | `/` | full page | any |
| Create chore | `GET`/`POST` | `/chores/new/` | full page / redirect | parent |
| Edit chore | `GET`/`POST` | `/chores/<id>/edit/` | full page / redirect | parent |
| Claim chore | `POST` | `/instances/<id>/claim/` | fragment: updated chore row | family member |
| Mark done | `POST` | `/instances/<id>/done/` | fragment: updated chore row | family member (owner) |
| Approval queue | `GET` | `/approvals/` | full page | parent |
| Approve completion | `POST` | `/instances/<id>/approve/` | fragment: updated row | parent |

Update this table (URL, exact fragment returned) as each corresponding
task in the GitHub issue backlog is implemented -- treat it as documenting
what was actually built, not a spec to build ahead of the issues.
