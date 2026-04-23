# Git Naming Conventions

This document outlines the standard naming conventions for Issues, Branches, Pull Requests and commits in the project. These rules have been established to enhance traceability, reduce redundancy, and improve our overall developer experience and automated tooling.

For the rationale behind these rules, see the [ADR: Branch, Pull Request, and Issue Naming Conventions](../adr/20260421-git-naming).

---

## 1. Issues

**Rule:** Descriptive Title Only

* **Format:** `Descriptive Title Here`
* **Example:** `Fix login bug`
* **Details:** Keep the issue title simple and descriptive of the problem or feature. Do not include prefixes like `Bug:` or `Feature:` in the title, as the type and scope of the issue are tracked using GitHub **labels**. Labels are mandatory and should be used to indicate both the type of issue (e.g., `bug`, `feature`, `chore`) and the scope (e.g., `backend`, `frontend`, `ml`).

---

## 2. Branches

**Rule:** Minimal with Scope

* **Format:** `scope/issue-number-short-desc`
* **Example:** `backend/123-fix-login-bug`
* **Details:**
  * **scope**: Grouping branches by scope (e.g., `backend`, `frontend`, `ml`, `devops`) makes it easy to filter and navigate branches using autocomplete.
  * **issue-number**: Placing the issue number immediately after the slash ensures it is reliably extractable by CI/CD scripts.
  * **short-desc**: A brief, hyphen-separated description of the work.

---

## 3. Pull Requests

**Rule:** Conventional Commits Style

* **Format:** `type(scope): short-desc`
* **Example:** `fix(auth): resolve token expiration issue`
* **Details:** PR titles are squash-merged and displayed as commits in the repository history, so they must follow the Conventional Commits specification.
  * **type**: Should map to the issue label (e.g., `feat`, `fix`, `chore`, `docs`, `refactor`).
  * **scope**: Should indicate the area of the codebase affected (e.g., `auth`, `ui`, `api`).
  * **short-desc**: A concise description of the change.

---

## 4. Commits

**Rule:** Conventional Commits Style

* **Format:**

  ```text
  type(scope?): subject
  ```

* **Example:**

  ```text
  feat(api): add user authentication endpoint
  ```

* **Details:** We follow the standard [Conventional Commits](https://www.conventionalcommits.org/) specification.
  * **type**: Defines the intent of the commit. Common types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
  * **scope**: (Optional but recommended) Defines what section of the codebase the commit affects.
  * **subject**: A short, imperative tense description of the change. Do not capitalize the first letter, and no dot (`.`) at the end.

By keeping these structures strictly adhered to, we maintain a clean Git history and enable better tracking from Issue to PR to deployment.
