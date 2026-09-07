# Shared Household Chore Manager --- Task Backlog

This backlog breaks the MVP (see `_docs/plan.md` and `_docs/architecture.md`)
into small, independent tasks. Each task is scoped to be finishable in a
single session and described with enough context to hand to someone who
hasn't read the others or the surrounding docs in depth.

Stack assumed throughout: Django + PostgreSQL (see `_docs/architecture.md`).

## 1. Project Setup with a Passing Test

Goal: Have an empty Django project that runs and has one passing test.

Description: Create a new Django project and a single app (e.g. `chores`),
configure it to use PostgreSQL, and commit a minimal `settings.py`. Add one
trivial test (e.g. asserting the home page returns a 200, or `1 == 1` if no
view exists yet) and confirm `manage.py test` passes, so future tasks have a
working CI-able baseline to build on.

## 2. Household and FamilyMember Models

Goal: Model who belongs to which household and what role they have.

Description: Add a `Household` model and a `FamilyMember` model that extends
or links to Django's user model, including a `role` field (parent or family
member) and a foreign key to `Household`. Write migrations and a couple of
model tests confirming a household can have multiple members with different
roles.

## 3. Login for Parents and Family Members

Goal: Let any family member log in to see the app.

Description: Implement a simple login flow (Django's built-in auth is
sufficient) that authenticates a `FamilyMember` and redirects to a
placeholder home page. Household/role-specific behavior is not required
here --- just get a working login/logout flow with a test covering a
successful and a failed login attempt.

## 4. ChoreDefinition Model and Admin Registration

Goal: Let a chore's reusable definition be stored and inspected.

Description: Add a `ChoreDefinition` model capturing name, point value,
ownership type (assigned vs. claimable), assigned family member (nullable),
recurrence rule (a simple text/choice field is fine for now, e.g. "daily",
"weekly:tuesday"), and verification mode (instant vs. parent approval).
Register it in the Django admin so definitions can be created/edited without
a custom UI yet, and add a model test or two for basic field validation.

## 5. ChoreInstance Model

Goal: Represent one day's actual occurrence of a chore, separate from its
recurring definition.

Description: Add a `ChoreInstance` model with a foreign key to
`ChoreDefinition`, a date, and a status field (available, claimed, pending
approval, completed, missed). This is the row that claiming, completion, and
approval will operate on in later tasks. Include a migration and a test
confirming a `ChoreInstance` can be created linked to a `ChoreDefinition`.

## 6. Parent: Create a Chore

Goal: Let a parent create a new chore definition through the UI.

Description: Build a form-backed view, restricted to users with the parent
role, for creating a `ChoreDefinition` (name, points, assigned vs. claimable,
assigned member if applicable, recurrence, verification mode). On save,
redirect to a simple confirmation or listing page. Include a test verifying
a non-parent cannot access this view.

## 7. Parent: View and Edit Existing Chores

Goal: Let a parent see all chore definitions for their household and edit
one.

Description: Build a list view showing every `ChoreDefinition` in the
parent's household, and an edit view/form reusing the same fields as chore
creation. Restrict both to the parent role. Add a test confirming a parent
only sees chores belonging to their own household, not another household's.

## 8. Family Member Dashboard: Today's Chores

Goal: Show a family member what's assigned to them today.

Description: Build a dashboard view that queries `ChoreInstance`s for the
current day belonging to the logged-in family member (status
available/claimed/pending, owned by them) and renders them in a simple list.
Assume some `ChoreInstance` rows already exist in the database (via admin or
fixtures) --- generating them automatically is a separate task. Include a
test with a couple of instances confirming only the logged-in member's
chores appear.

## 9. Dashboard: Available Chores Pool

Goal: Show claimable chores that no one has claimed yet.

Description: Extend or add to the dashboard a section listing
`ChoreInstance`s that are claimable and still in `available` status,
regardless of which family member is logged in. Each entry should show the
chore name and point value. Add a test confirming a claimed or completed
instance does not appear in this list.

## 10. Claim a Chore (Atomic, First-to-Claim)

Goal: Let a family member claim an available chore, safely under
concurrent attempts.

Description: Implement a "claim" action that transitions a `ChoreInstance`
from `available` to `claimed` and assigns it to the requesting family
member, wrapped in a database transaction with a status check so two
simultaneous claims can't both succeed. Add a test that simulates two claim
attempts on the same instance and asserts only one succeeds.

## 11. Mark a Chore Done (Instant Completion Path)

Goal: Let a family member complete a chore that doesn't need approval.

Description: Implement a "mark done" action on a `ChoreInstance` whose
`ChoreDefinition.verification_mode` is instant: transition the instance to
`completed`, create a `Completion` record, and award the chore's points to
the family member. Add a test confirming points are awarded exactly once
per completion.

## 12. Mark a Chore Done (Parent Approval Path)

Goal: Let a family member submit a chore for parent approval instead of
instant completion.

Description: Implement the branch of "mark done" for chores whose
`ChoreDefinition.verification_mode` requires approval: transition the
`ChoreInstance` to `pending_approval` instead of `completed`, without
awarding points yet. Add a test confirming no points are awarded until a
separate approval step (task 13) occurs.

## 13. Parent Approval Queue

Goal: Let a parent review and approve chores pending verification.

Description: Build a view, restricted to the parent role, listing all
`ChoreInstance`s in `pending_approval` status for their household, with an
approve action that transitions the instance to `completed`, creates the
`Completion` record, and awards points. Add a test confirming approval
awards points and updates status correctly.

## 14. Recurring Chore Expansion Job

Goal: Automatically create today's `ChoreInstance` from each active
recurring `ChoreDefinition`.

Description: Write a Django management command that, for each
`ChoreDefinition` with a recurrence rule matching today, creates a
`ChoreInstance` for today if one doesn't already exist. This command is
intended to be run daily via a scheduled job (cron), but wiring up the
actual scheduler is out of scope for this task. Add a test running the
command twice and confirming it doesn't create duplicate instances.

## 15. Missed Chore Marking Job

Goal: Mark yesterday's incomplete chores as missed.

Description: Write a management command (can be a second command or added
to task 14's command) that finds `ChoreInstance`s from prior days still in
`available`, `claimed`, or `pending_approval` status and transitions them to
`missed`. Add a test confirming a completed instance is left untouched while
an incomplete one is marked missed.

## 16. Streak Tracking

Goal: Track each family member's current streak per recurring chore.

Description: Add a `StreakRecord` model (family member + chore definition +
current streak count + best streak) and update it whenever a `ChoreInstance`
is completed (increment) or marked missed (reset to zero) for that
definition. Add tests covering both an increment on completion and a reset
on a missed occurrence.

## 17. Display Streaks on the Dashboard

Goal: Show each family member's current streaks alongside their chores.

Description: Extend the family member dashboard (task 8) to display the
current streak count next to any chore definition that has an associated
`StreakRecord` with a non-zero streak. Add a test confirming the streak
number rendered matches the underlying `StreakRecord`.

## 18. Reward Model and Parent Management UI

Goal: Let a parent define rewards and their point/streak thresholds.

Description: Add a `Reward` model (name, description, point threshold
and/or streak threshold) and a simple parent-only CRUD UI for creating and
listing rewards for their household. Add a test confirming a non-parent
cannot create a reward.

## 19. Reward Progress Display

Goal: Show family members how close they are to unlocking each reward.

Description: On the family member's dashboard, list each household reward
alongside the member's current point total (and relevant streak, if the
reward has a streak threshold), showing progress toward the threshold. Add a
test confirming the displayed progress matches the member's actual points/
streak values.

## 20. Points Summary Across Family Members

Goal: Show a shared view of every family member's current point total.

Description: Add a dashboard section (visible to all roles) listing each
family member in the household with their total points earned to date, as
described in the plan's example dashboard. Add a test confirming totals sum
completions correctly for each member independently.
