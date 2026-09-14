Stack

- Django + PostgreSQL, managed with `uv`, tested with `pytest` (via
  `pytest-django`) rather than `manage.py test`. See `_docs/architecture.md`
  for the full rationale.

Commands

- `uv sync` - install dependencies
- `uv run pytest` - the whole suite
- `uv run pytest tests/test_home.py` - one test file
- `uv run manage.py <command>` - Django management commands (migrations,
  the recurrence/missed-chore jobs, etc.)

Rules

- Dependencies are added in `pyproject.toml`. Do not add one without asking


Documents

- `_docs/process.md` - how work is organized
- Before writing tests, read `_docs/testing-guidelines.md`
- For anything touching the UI, read `_docs/design-system.md`
- For anything related to api, read `_docs/api.md`