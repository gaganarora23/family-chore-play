"""Reward progress computation (#22).

Design decisions this task makes, since the plan doesn't specify them:

- A reward with *both* `point_threshold` and `streak_threshold` set is
  "unlocked" only once **both** are met, not either -- each threshold the
  parent adds is treated as an additional requirement, not an
  alternative route to the same reward.
- `Reward` has no link to a specific `ChoreDefinition`, so "the relevant
  streak" for a `streak_threshold` is the member's single highest active
  streak across all their chores (`FamilyMember.best_current_streak()`),
  not any one chore in particular.
"""


def reward_progress_for(family_member):
    """Every household Reward with the member's progress toward each one.

    Returns a list of dicts: `reward`, `points_progress` (a
    `(current, threshold)` pair, or `None` if the reward has no
    `point_threshold`), `streak_progress` (likewise), and `unlocked`.
    """
    from .models import Reward

    total_points = family_member.total_points()
    best_streak = family_member.best_current_streak()
    progress = []
    for reward in Reward.objects.filter(household=family_member.household):
        points_progress = None
        streak_progress = None
        unlocked = True
        if reward.point_threshold is not None:
            points_progress = (total_points, reward.point_threshold)
            unlocked = unlocked and total_points >= reward.point_threshold
        if reward.streak_threshold is not None:
            streak_progress = (best_streak, reward.streak_threshold)
            unlocked = unlocked and best_streak >= reward.streak_threshold
        progress.append(
            {
                'reward': reward,
                'points_progress': points_progress,
                'streak_progress': streak_progress,
                'unlocked': unlocked,
            }
        )
    return progress
