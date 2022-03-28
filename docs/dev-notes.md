# Development notes

## Implementation framework

This project is implemented using 
[Plotly Dash](https://dash.plotly.com/introduction).

Dash enables the programmer to code applications with behaviour 
like that of a single page app entirely on the server side in Python.
Behind the scenes, Dash creates a React app and a backend for the app to 
interact with.

Dash's design means that a Dash app constantly interacts with the app's
backend, even for trivial interactions with the user.
Its design also includes exchanging all data between backend and frontend as
JSON.

## Map component sluggishness

Design Value Explorer, which presents large amounts of data (spatial rasters)
in the map component, reveals the shortcomings of Dash's design: Updates to the 
map are very slow.

A more responsive app could be achieved in one of two related ways:

- Code one or more custom Dash-wrapped React components for this app that 
  use Leaflet or other mapping software to display the DV rasters.
- Re-implement DVE with a standard frontend - backend architecture (like 
  most of our web apps), using Leaflet or other mapping software to display 
  the DV rasters.

Both alternatives would require setting up an ncWMS instance to serve 
the DV rasters as map tiles, and probably also require modifying the DV 
raster files for consumption by ncWMS. There are probably other 
complications, but this is the main one associated with these solutions.

Both alternatives have thus far been rejected as costing too much 
time and effort for the anticipated gain, given the relatively small and 
specialized user base of DVE.

## Map-click sluggishness

The map-click data display (for potential download) is also quite slow.
This is due in part to the design of this app (not Dash itself), which must 
extract values from many separate DV files to fill the table. Significant 
effort was expended to cache these file accesses. This improved 
responsiveness, but not to the point of sprightliness. In the end, the data 
design imposes an unavoidable bottleneck.

It's not clear whether there is a viable alternative to this data design.

It's also not clear whether a non-Dash implementation could do better; this 
is more a function of data access on the backend than data communications.

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

