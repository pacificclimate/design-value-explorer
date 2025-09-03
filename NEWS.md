# News / Release Notes

## 2.4.1

- Updated Table C-2 RAnn values. Change factors for RAnn modified to maintain consistency with future PAnn totals.

## 2.4.0

A couple of important new features in this release:
- Multilingual (French, English)
- Set design variable from query parameter, and vice-versa, making it easier for a user to send a link that highlights specific data. 

Updates:
- [Set design variable from query parameter](https://github.com/pacificclimate/design-value-explorer/pull/233)
- [Support multiple languages; add French](https://github.com/pacificclimate/design-value-explorer/pull/230)
- [Update internal documentation](https://github.com/pacificclimate/design-value-explorer/pull/228)

## 2.3.0

Updates:
- [Add deployment automation](https://github.com/pacificclimate/dash-dv-explorer/pull/227)

## 2.2.0

Initial production release.

Updates:
- [Log key performance indicators](https://github.com/pacificclimate/dash-dv-explorer/pull/223)
- [Documentation and presentation updates](https://github.com/pacificclimate/dash-dv-explorer/pull/217)
- [Fix Pipfile](https://github.com/pacificclimate/dash-dv-explorer/pull/220)
- [Update graph and table titles with Tier info](https://github.com/pacificclimate/dash-dv-explorer/pull/216)
- [Update documentation; improve behaviour on no data](https://github.com/pacificclimate/dash-dv-explorer/pull/211)
- [Add logo and favicon; improve layout](https://github.com/pacificclimate/dash-dv-explorer/pull/210)

## 2.1.3

**2021-Nov-26**

Draft production candidate. Fixes double-update problem.

## 2.1.2

**2021-Nov-25**

Draft production candidate. 
Bumps local_preferences version to force update which prevents errors.

## 2.1.1

**2021-Nov-25**

Draft production candidate. Bugfix update.

Updates:
- [Handle unitless DVs](https://github.com/pacificclimate/dash-dv-explorer/pull/204)
- [Fix errors creating map-click download table](https://github.com/pacificclimate/dash-dv-explorer/pull/203)
- [Fix errors in callbacks for MI, future](https://github.com/pacificclimate/dash-dv-explorer/pull/200)

## 2.1.0

**2021-Nov-25**

Draft production candidate.

Updates:
- [Use precomputed CFs in Table C2](https://github.com/pacificclimate/dash-dv-explorer/pull/198)
- [Fix CF file paths for 2.5, 3.5](https://github.com/pacificclimate/dash-dv-explorer/pull/197)

## 2.0.0

**2021-Oct-25**

Draft production candidate.

Feature updates:
- [Add About tab](https://github.com/pacificclimate/dash-dv-explorer/pull/195)
- [Add Help tab](https://github.com/pacificclimate/dash-dv-explorer/pull/193)
- [Remove Masks control](https://github.com/pacificclimate/dash-dv-explorer/pull/191)
- [Revise layout](https://github.com/pacificclimate/dash-dv-explorer/pull/186) - New layout; better adaptive layout.
- [Turn off and disable Station ctrl for future datasets](https://github.com/pacificclimate/dash-dv-explorer/pull/185)
- [Put map and colorbar in single Graph object](https://github.com/pacificclimate/dash-dv-explorer/pull/182)
- [Establish local preferences](https://github.com/pacificclimate/dash-dv-explorer/pull/179)
- [Fix config for scale](https://github.com/pacificclimate/dash-dv-explorer/pull/178)
- [Use separate color mapping for future vs historical](https://github.com/pacificclimate/dash-dv-explorer/pull/177)

Technical updates:
- [Refactor config files with YAML !includes](https://github.com/pacificclimate/dash-dv-explorer/pull/192)
- [Fix local preferences for DVs with ids containing "."](https://github.com/pacificclimate/dash-dv-explorer/pull/189)
- [Code and documentation cleanup](https://github.com/pacificclimate/dash-dv-explorer/pull/187)
- [Refactor local config](https://github.com/pacificclimate/dash-dv-explorer/pull/184)
- [Refactor config file](https://github.com/pacificclimate/dash-dv-explorer/pull/175)

## 1.4.4

**2021-Sep-21**

- Fix heatmap zmin, zmax (color mapping bounds)

## 1.4.3

**2021-Sep-21**

- Fix error in python-ci

## 1.4.2

**2021-Sep-21**

- [Fix colorscale](https://github.com/pacificclimate/dash-dv-explorer/pull/174)

## 1.4.1

**2021-Aug-05**

Internal evaluation release. Changes to date:

- [Map colourscale threshold - no change](https://github.com/pacificclimate/dash-dv-explorer/issues/127)
- [Round colourbar annotations like all other reported values - adjustment](https://github.com/pacificclimate/dash-dv-explorer/issues/139)

## 1.4.0

**2021-Aug-04**

Internal evaluation release. Changes to date:

- [Apply Black](https://github.com/pacificclimate/dash-dv-explorer/pull/155)
- [Round colorbar annotations](https://github.com/pacificclimate/dash-dv-explorer/pull/154)
- [Don't update download table when DV changes](https://github.com/pacificclimate/dash-dv-explorer/pull/153)
- [Improve table loading spinners](https://github.com/pacificclimate/dash-dv-explorer/pull/150)
- [Improve Docker security in dev-local](https://github.com/pacificclimate/dash-dv-explorer/pull/149)
- [Update only selected tab](https://github.com/pacificclimate/dash-dv-explorer/pull/148)
- [Improve map behaviour with lat-lon grid](https://github.com/pacificclimate/dash-dv-explorer/pull/147)
- [Upgrade plotly, Dash; install orjson](https://github.com/pacificclimate/dash-dv-explorer/pull/146)
- [Improve log scale colourbar](https://github.com/pacificclimate/dash-dv-explorer/pull/145)

## 1.3.1

**2021-Mar-30**

Small but important improvements

- [Fix map hover popup text](https://github.com/pacificclimate/dash-dv-explorer/pull/144)
- [Shorten map title](https://github.com/pacificclimate/dash-dv-explorer/pull/143)

## 1.3.0

**2021-Mar-30**

Beta Release!

- [Use appropriate rounding in Table C2 CFs](https://github.com/pacificclimate/dash-dv-explorer/pull/136)
- [Update Table C2 labels](https://github.com/pacificclimate/dash-dv-explorer/pull/134)
- [Download only reconstruction values](https://github.com/pacificclimate/dash-dv-explorer/pull/131)
- [Add change factors to Table C2](https://github.com/pacificclimate/dash-dv-explorer/pull/130)
- [Pre release cleanup](https://github.com/pacificclimate/dash-dv-explorer/pull/124)
- [Fix units in download files](https://github.com/pacificclimate/dash-dv-explorer/pull/123)
- [Access files under cache thread lock](https://github.com/pacificclimate/dash-dv-explorer/pull/122)
- [Precision of reported values](https://github.com/pacificclimate/dash-dv-explorer/pull/119)
- [Reduce grid density (config)](https://github.com/pacificclimate/dash-dv-explorer/pull/117)
- [Add control to turn on/off grid lines](https://github.com/pacificclimate/dash-dv-explorer/pull/116)
- [Always show map modebar (configurable)](https://github.com/pacificclimate/dash-dv-explorer/pull/115)
- [Add climate regime to map label](https://github.com/pacificclimate/dash-dv-explorer/pull/112)
- [Update labelling](https://github.com/pacificclimate/dash-dv-explorer/pull/110)
- [Include IDF CFs as DVs; fix data access problems](https://github.com/pacificclimate/dash-dv-explorer/pull/95)
- [Add several missing CFs](https://github.com/pacificclimate/dash-dv-explorer/pull/92)


## 1.2.0

**2021-Mar-18**

Major new feature: Show and download future change factor values.

Minor, but important, new feature: Show loading spinners.

- [Validate config](https://github.com/pacificclimate/dash-dv-explorer/pull/89)
- [Control DVs available more simply in config](https://github.com/pacificclimate/dash-dv-explorer/pull/88)
- [Add loading spinners](https://github.com/pacificclimate/dash-dv-explorer/pull/85)
- [Add change factors](https://github.com/pacificclimate/dash-dv-explorer/pull/81)

## 1.1.2

**2021-Mar-15**

- [Fix download button](https://github.com/pacificclimate/dash-dv-explorer/pull/80)

## 1.1.1

**2021-Mar-15**

Main change: Load data only on demand.

- [Load data only on demand](https://github.com/pacificclimate/dash-dv-explorer/pull/78)
- [Partial fix for security vulnerabilities](https://github.com/pacificclimate/dash-dv-explorer/pull/75)


## 1.1.0

**2021-Mar-11**

Main new feature: Add NBCC 2015 values to table C2.

- [Add NBCC 2015 values to table C2](https://github.com/pacificclimate/dash-dv-explorer/pull/73)
- [Fix various UI annonyances](https://github.com/pacificclimate/dash-dv-explorer/pull/72)
- [Add info re DASH_URL_BASE_PATHNAME (production deployment update)](https://github.com/pacificclimate/dash-dv-explorer/pull/71)
- [Don't use modifiable global variables in callbacks](https://github.com/pacificclimate/dash-dv-explorer/pull/70)


## 1.0.0

**2021-Mar-09**

First production-ready release. 
Contains some but not all beta release features; beta feature changes are 
marked with an asterisk.

- [Increase no. of lines of lat, long upon zoom](https://github.com/pacificclimate/dash-dv-explorer/pull/65) *
- [Apply Python Black](https://github.com/pacificclimate/dash-dv-explorer/pull/62)
- [Set colour palette selection according to DV](https://github.com/pacificclimate/dash-dv-explorer/pull/61) *
- [Full production deployment (Gunicorn)](https://github.com/pacificclimate/dash-dv-explorer/pull/60)
- [Set scale control according to DV](https://github.com/pacificclimate/dash-dv-explorer/pull/57) *
- [Preliminary production deploy](https://github.com/pacificclimate/dash-dv-explorer/pull/55)
- [Add descriptions and units to config](https://github.com/pacificclimate/dash-dv-explorer/pull/53) *
- [Fix layout for narrower windows](https://github.com/pacificclimate/dash-dv-explorer/pull/52)
- [Remove Raster switch](https://github.com/pacificclimate/dash-dv-explorer/pull/49) *
- [Add data download](https://github.com/pacificclimate/dash-dv-explorer/pull/46) *
- [Add at-hover display with lat, lon, DV](https://github.com/pacificclimate/dash-dv-explorer/pull/42) *
- [Add DV descriptions](https://github.com/pacificclimate/dash-dv-explorer/pull/40) *
- [Simplify colourbar ticks](https://github.com/pacificclimate/dash-dv-explorer/pull/39) *
- [More dev cleanup](https://github.com/pacificclimate/dash-dv-explorer/pull/38)
- [Dev cleanup](https://github.com/pacificclimate/dash-dv-explorer/pull/32)
- [Mount data files externally](https://github.com/pacificclimate/dash-dv-explorer/pull/30)

## 0.1dev

**2020-Dec-23**

Development release for evaluation. Not ready for production deployment.