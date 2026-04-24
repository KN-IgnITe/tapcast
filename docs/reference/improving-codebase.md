# Issue assigned to issue resolved

Being assigned an issue means that you are expected to resolve it. Below is the full process of resolving an issue, from the moment you are assigned to it until it is closed.

## 1. **Understand the issue**

Read the issue description carefully, and if you have any questions, ask for clarification in the issue comments.
If the issue is marked as `blocked`, see [Working on issues with `blocked` status](working-on-blocked-issues.md) for more details.

If you decide that the issue demands architectural decisions to be made, you can [Ask a Question](../how-to/ask-a-question.md) to get help from the team.

> At this stage you should be assigned to the issue.

## 2. **Create a branch**

Once you understand the issue, create a branch for it. The issue page has a "Create Branch" button that will create a branch.

Make sure to follow the [Git Naming Conventions](git-naming-conventions.md#2-branches) when naming your branch.

> At this stage the issue should be moved to the "In Progress" column in the project board.

## 3. **Work on the issue**

Make the necessary code changes to resolve the issue. Make sure to write tests for your changes if applicable.

You are expected to follow the [Git Naming Conventions](git-naming-conventions.md#4-commits) when naming your commits.

>At this stage the issue should be moved to the "In Progress" column in the project board.

## 4. **Create a Pull Request**

Once you have made the necessary changes, create a Pull Request (PR) to merge your branch into the `development` branch.

Make sure to follow the [Git Naming Conventions](git-naming-conventions.md#3-pull-requests) when naming your PR.

> At this stage the issue should be moved to the "In Review" column in the project board.

## 5. **Get the Pull Request reviewed**

Have your PR reviewed by a team member. Address any feedback and make necessary changes.
If your PR receives a request for changes, make the necessary changes and ask for re-review.

> At this stage the issue should be moved to the "In Review" column in the project board.
> If the PR receives a request for changes, the issue should be moved back to the "In Progress" column in the project board.

## 6. **Merge the Pull Request**

Once your PR is approved, it will be merged into the `development` branch.

> At this stage the issue should be moved to the "Done" column in the project board, and the issue and PR should be closed.
