# ADR: Remote-Enforced CI with Path-Filtering (Temporary Solution)

## Status

Accepted (Temporary)

## Context

Currently, verifying Pull Requests requires reviewers to either trust the author's word that tests pass, or manually check out the branch and run tests locally. We needed to evaluate the best approach between a completely remote-enforced CI and local testing.

While setting up GitHub Actions with `dorny/paths-filter` solves the immediate problem of remote verification and compute efficiency, it introduces two structural issues:

1. **Configuration Drift:** Having separate configurations for local pre-commits (`lefthook.yaml`) and remote CI (`.github/workflows/pr-tests.yml`) means versions and rules can easily fall out of sync.
2. **Missing Integration Tests:** The current setup only triggers unit tests and linters, leaving integration tests out of the automated pipeline.

## Decision

We decided to implement the GitHub Actions path-filtering workflow as an **acceptable, temporary step forward**. It is significantly better than having no remote CI at all.

However, to address configuration drift, we establish that this is not the final state. We will research and transition to a Single Source of Truth (SSoT) architecture for all CI checks.

## Future Exploration (SSoT)

To achieve a Single Source of Truth and include integration tests, we will explore:

* Executing `lefthook run` directly within the GitHub Actions runners to unify local and remote checks under one configuration file.
* Utilizing containerized CI/CD tools (e.g., Earthly, Dagger) to guarantee identical pipeline execution locally and remotely.
* Expanding the pipeline to provision necessary databases/services for full integration testing.

## Consequences

* **Positive:** Immediate, drastic improvement in PR verification and reviewer experience.
* **Positive:** Minimized CI compute costs and feedback loop times.
* **Negative (Technical Debt):** Temporary configuration drift exists between Lefthook and GitHub Actions until the SSoT solution is researched and implemented.
