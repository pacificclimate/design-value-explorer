# Development notes

## Dash versions

In [PR #220](https://github.com/pacificclimate/dash-dv-explorer/pull/220),
the `Pipfile` was updated to an installable and modifiable state.
(For problem details, 
[Issue #219](https://github.com/pacificclimate/dash-dv-explorer/issues/219)).

The takeaway from this exercise is that Dash > 2.0.0 and associated other 
updated Dash package versions cause a malfunction in the app. Updating Dash 
will require some extra work to fix this.

Details of Pipfile update process:

1. Unpin all versions in `Pipfile`.
   1. Set all package version specifiers to `*`.
   2. Run `pipenv lock`.
   3. Build and start new `dve-dev-local` Docker image/container.
   4. Result: App is broken.
2. Pin (only) versions of Dash packages.
   1. Set Dash package version specifiers to _pre_-update versions.
   2. Run `pipenv lock`.
   3. Build and start new `dve-dev-local` Docker image/container.
   4. Result: App works.
3. Pin versions of remaining packages.
   1. Set remaining package version specifiers to _post_-update versions 
      (as listed by `pip freeze`).
   2. Run `pipenv lock`.
   3. Build and start new `dve-dev-local` Docker image/container.
   4. Result: App works.

