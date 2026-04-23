# Branch, Pull Request, and Issue Naming Conventions

* Status: accepted
* Date: 2026-04-21
* Deciders: Mikołaj Popik, Maciej Frąckiewicz, Grzegorz Maciaszek, Oliwia Guzik

## Context and Problem Statement

Currently, there may be a lack of standardization in how branches, pull requests (PRs), and issues are named. This inconsistency leads to redundancy, makes it harder to track work, and complicates the CI/CD or release management processes. We need a standardized naming convention to streamline workflows, improve readability, and ensure traceability from an issue to its corresponding PR and branch, while avoiding redundant data.

## Decision Drivers

* Need for clear traceability between issues, branches, and PRs.
* Desired reduction in redundant information (e.g., avoiding repeating the issue title everywhere).
* Improving developer experience and onboarding via standardized, predictable practices.
* Compatibility with automated tooling (e.g., GitHub Actions, semantic release).

## Considered branch name options

* Option 1: Conventional Commits/Type-based (e.g., `type/issue-number-short-desc`)
* Option 2: Minimal Issue ID Prefix (e.g., `issue-number-short-desc`)
* Option 3: Minimal with Scope (e.g., `scope/issue-number-short-desc`)
* Option 4: Developer-scoped (e.g., `username/type/issue-number`)

### Branches: Decision Outcome

Chosen option: **Option 3: Minimal with Scope (e.g., `scope/issue-number-short-desc`)**, because it puts the issue number in a reliable place for automation, aligns with autocompletion when searching for branches in a specific team and minimizes clutter

### Branches: Positive Consequences

* **Improved search and navigation:** Grouping branches by scope makes it much easier to filter and navigate branches using autocomplete in Git and Git UIs.
* **Streamlined automation:** The consistent placement of the issue number directly after the scope slash (`/`) makes it very reliable for CI/CD scripts to extract and link to issue trackers.
* **Reduced visual noise:** Keeps branch names concise without repeating redundant information, focusing only on where (scope) and what (issue-number-short-desc).

### Branches: Negative Consequences

* **Missing work type context:** Unlike pattern-based conventional commits (e.g., `feat/`, `fix/`), the branch name doesn't immediately indicate if the work is a bug, feature, or chore.
* **Requires strict enforcement:** The team must maintain discipline, or set up automated checks/git hooks, to ensure branches adhere strictly to the chosen format without typos.

## Considered PR title options

* Option 1: Full Issue Title (e.g., `Fix login bug`)
* Option 2: Issue Number + Short Description (e.g., `#1234 Fix login bug`)
* Option 3: Issue Number Only (e.g., `#1234`)
* Option 4: Conventional Commits Style (e.g., `type(scope): short-desc`)

### PRs: Decision Outcome

Chosen option: **Option 4: Conventional Commits Style (e.g., `type(scope): short-desc`)**, because it later displays
as a commit in the commit history and should be named as such. Type should be taken from the issue label.

### PRs: Positive Consequences

* **Immediate context:** The PR title clearly indicates the type of change (e.g., `feat`, `fix`) and the scope, providing immediate context to reviewers.

* **Consistency with commit messages:** Aligning PR titles with conventional commit styles ensures that the PR title can be directly used as a commit message, maintaining consistency across the development workflow.

### PRs: Negative Consequences

* **Requires discipline:** Developers must ensure that the PR title follows the conventional commit format, which may require additional training or reminders.

## Considered Issue title options

* Option 1: Descriptive Title Only (e.g., `Fix login bug`)
* Option 2: Type + Descriptive Title (e.g., `Bug: Fix login bug`)
* Option 3: Type + Scope + Descriptive Title (e.g., `Bug(Auth): Fix login bug`)

### Issues: Decision Outcome

Chosen option: **Option 1: Descriptive Title Only (e.g., `Fix login bug`)**, because type/scope is already represented by labels.

### Issues: Positive Consequences

* **Simplicity:** A descriptive title is straightforward and easy to understand without needing to parse additional metadata.
* **Reduced redundancy:** Since the type and scope are represented by labels, including them in the title would be redundant and cluttered.

### Issues: Negative Consequences

* **Uniformity loss:** Without a structured format, issue titles may vary widely in style and clarity, potentially making it harder to quickly identify the nature of the issue at a glance.

## Conclusion

By adopting the chosen naming conventions for branches, PRs, and issues, we aim to enhance traceability, reduce redundancy, and improve the overall developer experience. The branch naming convention will facilitate better organization and automation, while the PR title format will provide clear context for reviewers. The issue title format will keep things simple and focused on the descriptive aspect, relying on labels for additional metadata.
