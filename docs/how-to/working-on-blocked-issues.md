# Working on issues with `blocked` status

When an issue is marked as `blocked`, it indicates that work on the issue cannot proceed until certain other issues are resolved.

You are not required to work on `blocked` issues until the blockers are resolved, and will not be expected to make progress on them until then.

The `blocked` tag means that there exists some part of work that cannot be done until the blockers are resolved, but there may be other parts of the issue that can be done in the meantime.

You can start working on the parts that are not blocked, create the issue branch and make a draft PR.
If you want to do so, keep in mind:

- The PR should be marked as a draft. That prevents it from being merged before being fully complete.
- There is a high chance of you not being able to run any tests of your code, so be ready to change things once the blockers are resolved.
- Once the blockers are resolved, you will have to rebase your branch to get the blocker resolutions.

Happy working :)
