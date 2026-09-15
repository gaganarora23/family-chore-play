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
