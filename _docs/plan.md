# Shared Household Chore Manager --- MVP Plan

## 1. Product Goal

Build a simple website for families to manage shared household chores.

The primary goals are:

1.  Reduce the need for parents to repeatedly remind family members
    about chores.
2.  Motivate participation through points, streaks, and rewards.

The MVP is intended for the whole family: parents and children.

## 2. Product Principle

**Make chores happen without parents constantly reminding everyone ---
and make participation rewarding.**

The core loop is:

**Chore → Points → Streaks → Rewards**

## 3. Platform

For the MVP, the product will be a **simple responsive website**.

Native mobile apps, NFC integrations, and other interfaces are out of
scope.

## 4. User Roles

### Parent

Parents manage the household chore system.

Parents can:

-   Create chores.
-   Assign chores to a specific family member.
-   Make chores available for family members to claim.
-   Set the point value for each chore.
-   Configure whether completion requires parent approval.
-   Configure recurring chores.
-   Approve chores that require verification.

Only parents can create chores in the MVP.

### Family Member / Child

Family members can:

-   View today's chores.
-   View chores assigned to them.
-   View available chores.
-   Claim available chores.
-   Mark their chores as completed.
-   Earn points.
-   Build streaks.
-   Progress toward rewards.

## 5. Dashboard

The dashboard is the primary home page.

It should provide a quick view of:

-   Today's chores.
-   Chores assigned to each family member.
-   Available chores that can be claimed.
-   Completed chores.
-   Family members' current points.
-   Reward progress.

Example:

``` text
TODAY
Maya
✓ Make Bed
  Dishwasher

Alex
✓ Feed Dog
  Take Trash Out

AVAILABLE TO CLAIM
Vacuum              +20 points
Laundry             +15 points

REWARDS
Maya                85 points
Alex                60 points
```

## 6. Chore Creation

Only parents can create chores.

When creating a chore, the parent defines:

-   Chore name.
-   Point value.
-   Whether the chore is assigned or claimable.
-   Assigned family member, when applicable.
-   Whether the chore is recurring.
-   Recurrence schedule.
-   Completion verification method.

There are two types of chore ownership.

### Assigned Chore

The parent assigns the chore directly to a family member.

Example:

> Take Trash Out → Alex → 10 points

### Claimable Chore

The chore is placed into a shared pool.

Example:

> Vacuum Living Room → Available → 20 points

Any family member can claim it.

## 7. Claiming Rules

Claimable chores use a **first-to-claim** model.

Example:

``` text
Vacuum Living Room
+20 points

[ Claim ]
```

The first family member who claims the chore owns it for that day.

Once a chore is claimed:

-   It is removed from the available pool.
-   It becomes that family member's responsibility.
-   It cannot be unclaimed for that day.

This makes claiming a commitment rather than a temporary reservation.

## 8. Chore Completion

A family member can mark their assigned or claimed chore as **Done**.

Each chore has one of two verification modes.

### Instant Completion

The system immediately:

-   Marks the chore complete.
-   Awards points.
-   Updates the streak.

### Parent Approval

The chore enters a pending state.

Example:

> Alex completed "Vacuum Living Room."

The parent can approve the completion.

After approval:

-   The chore becomes completed.
-   Points are awarded.
-   The streak is updated.

Verification is configured **per chore**.

## 9. Points

Each chore has a point value.

The **parent determines the point value**.

Examples:

  Chore                  Points
  -------------------- --------
  Make bed                    5
  Empty dishwasher           10
  Take trash out             10
  Laundry                    15
  Vacuum living room         20

The application does not automatically calculate or suggest point values
in the MVP.

## 10. Recurring Chores

The MVP supports recurring chores.

Examples:

-   Make bed every day.
-   Feed dog every day.
-   Take trash out every Tuesday.
-   Vacuum every Saturday.

Recurring chores automatically appear on the appropriate day.

The parent should not need to recreate these chores manually.

## 11. Deadlines

The MVP does **not** use specific times or deadlines.

A chore is simply due **Today**.

For example, the system will not support:

> Take trash out by 7:00 PM.

Instead:

> Take trash out --- Today.

This keeps scheduling and the user experience simple.

## 12. Missed Chores

If a recurring chore is not completed that day:

-   It is marked **Missed**.
-   The missed occurrence remains visible in history.
-   The family member's streak for that chore is broken.
-   The recurring chore can appear again on its next scheduled day.

A missed chore is therefore recorded rather than silently disappearing.

## 13. Streaks

Recurring chores can build streaks.

Example:

``` text
Make Bed
🔥 6-day streak
```

Completing the chore when scheduled continues the streak.

Missing the chore breaks the streak.

Streaks are part of the motivation system and can contribute to rewards.

## 14. Rewards

Points and streaks can unlock household rewards.

Possible rewards include:

-   Dessert.
-   Extra screen time.
-   Choosing the family movie.
-   Other family privileges.
-   Money for completing defined streak goals.

The MVP should support the basic relationship:

**Complete chores → Earn points → Build streaks → Unlock rewards**

A sophisticated rewards marketplace is not required.

## 15. Primary User Flow

### Parent Flow

``` text
Create Chore
     ↓
Set Point Value
     ↓
Choose Assigned or Claimable
     ↓
Configure Recurrence
     ↓
Choose Verification Method
     ↓
Chore Appears on Dashboard
```

### Family Member Flow

``` text
Open Dashboard
     ↓
View Today's Chores
     ↓
Complete Assigned Chore
        OR
Claim Available Chore
     ↓
Mark Chore Done
     ↓
Instant Completion
        OR
Wait for Parent Approval
     ↓
Earn Points
     ↓
Update Streak
     ↓
Progress Toward Reward
```

## 16. MVP Feature Summary

  Feature               MVP Decision
  --------------------- ----------------------------------------------------
  Target users          Whole family
  Primary problem       Reduce reminders + increase motivation
  Platform              Website
  Dashboard             Today's chores + available chores + points/rewards
  Chore creation        Parents only
  Assigned chores       Supported
  Claimable chores      Supported
  Claiming model        First person to claim
  Unclaiming            Not allowed that day
  Point values          Parent-defined
  Completion            User marks Done
  Verification          Configurable per chore
  Parent approval       Supported
  Recurrence            Supported
  Specific deadlines    Not supported
  Missed chores         Recorded in history
  Missed chore effect   Breaks streak
  Points                Supported
  Streaks               Supported
  Rewards               Supported

## 17. Explicitly Out of Scope

The following are intentionally excluded from the MVP:

-   Native iOS or Android apps.
-   NFC tags.
-   Photo proof of chore completion.
-   AI-generated chore suggestions.
-   AI point recommendations.
-   Push notifications.
-   SMS/email reminders.
-   Complex scheduling.
-   Specific completion times.
-   Calendar integrations.
-   Family chat or messaging.
-   Advanced leaderboards.
-   Sophisticated badges or gamification.
-   Complex reward marketplace.

These can be considered only after validating the basic chore-management
loop.

## 18. MVP Success Criterion

The MVP should successfully demonstrate this complete experience:

> A parent creates a recurring or one-time chore, assigns it or makes it
> claimable, a family member takes responsibility for it, completes it,
> receives points after any required approval, builds a streak, and sees
> progress toward a reward.

If that loop works clearly and reliably, the MVP has achieved its
purpose.

## 19. Next Design Step

Before selecting technologies or implementing the application, define
the minimum set of website screens.

The likely next exercise is to identify approximately **4--5 core
screens/pages**, determine what information belongs on each, and map the
navigation between them.
