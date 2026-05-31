# ADR: Remote-Enforced CI with Path-Filtering

## Status

Accepted

## Context

Currently, verifying Pull Requests requires reviewers to either trust the author's word that tests pass, or manually check out the branch and run tests locally. This local testing approach is time-consuming, prone to environment mismatches ("it works on my machine"), and disrupts the reviewer's workflow. We needed to evaluate the best approach between a completely remote-enforced CI and local testing. Furthermore, running the entire monolith test suite for every minor change is inefficient and wastes CI compute resources.

## Decision

We decided to shift from local-only testing to a completely remote-enforced CI pipeline using GitHub Actions. To optimize execution time and resource usage, we integrated the `dorny/paths-filter` action. This allows the CI to dynamically trigger specific test jobs (e.g., backend, frontend, inference, training) based exclusively on the paths of the modified files in a Pull Request. Local hooks (Lefthook) remain available for pre-commit checks, but GitHub Actions is now the ultimate source of truth.

## Consequences

* **Positive:** Reviewers can instantly see test results directly on the GitHub PR page without any local setup.
* **Positive:** CI compute costs and feedback loop times are minimized by only running relevant tests.
* **Positive:** Establishes a strict, automated quality gate before any code is merged.
* **Negative:** CI workflow files (`.github/workflows/`) will require occasional maintenance as the project structure evolves.
