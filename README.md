# family-chore-play

A shared household chore manager. See `_docs/plan.md` for the product plan,
`_docs/architecture.md` for the technical design, and `_docs/tasks.md` for
the MVP task backlog.

## Local development

Stack: Django + PostgreSQL (see `_docs/architecture.md`).

1. Create a virtualenv and install dependencies:

   ```sh
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```

2. Provide a PostgreSQL database, either a local install or a disposable
   container:

   ```sh
   docker run -d --name family-chore-play-pg \
     -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres \
     -e POSTGRES_DB=family_chore_play -p 5432:5432 postgres:16-alpine
   ```

3. Copy `.env.example` to `.env` (or otherwise export the same variables)
   and adjust as needed.

4. Run migrations and the test suite:

   ```sh
   .venv/bin/python manage.py migrate
   .venv/bin/python manage.py test
   ```
