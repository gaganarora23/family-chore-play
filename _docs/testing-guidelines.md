# Testing Guidelines

- Use pytest (via `pytest-django`), run with `uv run pytest` -- not
  `manage.py test`.
- Create test cases per task: each GitHub issue lists acceptance criteria
  and/or a specific test scenario (e.g. "confirm a non-parent cannot
  access this view") -- write a test for each one named after what it
  asserts, not just one broad test per model/view.
- Cover the negative/permission case as well as the happy path wherever
  an issue restricts an action by role (parent-only views, a family
  member only seeing their own household's data).
- Concurrency-sensitive logic gets a concurrency-specific test, not just
  a unit test of the happy path. The clearest example is claiming
  (issue #10 / plan §7): simulate two simultaneous claim attempts on the
  same `ChoreInstance` and assert exactly one succeeds and the other is
  rejected, not just that a single claim works.
- State-machine transitions (`available` -> `claimed` -> `completed` /
  `missed`, `pending_approval` -> `completed`) should each have a test
  confirming the specific transition, especially the ones that must NOT
  happen automatically (e.g. no points awarded until approval, per
  issue #12).
- Management commands (recurrence expansion, missed-chore marking) get a
  test that runs the command twice and confirms it's idempotent -- no
  duplicate `ChoreInstance` rows, no double-marking.
