# Process

- Tasks are GitHub issues, one at a time. Issues are the canonical, active
  backlog (`_docs/tasks.md` is a frozen historical snapshot only -- see
  the note at its top).
- Read the acceptance criteria before starting and before closing an
  issue -- both to scope the work and to confirm it's actually done.
- Work on a branch per issue, not directly on `main`.
- Commit regularly, with messages that reference the issue where useful.
- Open a PR per issue against `main`; merging the PR is what closes the
  loop on that task. Don't batch multiple issues into one PR unless
  they're trivially small and closely related.

  Roles

- PM - grooms a task before anyone implements it, follows _docs/team/pm.md
- Engineer - implements one groomed task, follows _docs/team/software-engineer.md
- QA - checks the result against the acceptance criteria, follows _docs/team/qa-engineer.md
