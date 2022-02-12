![Docker Publishing](https://github.com/pacificclimate/dash-dv-explorer/workflows/Docker%20Publishing/badge.svg)
[![Python CI](https://github.com/pacificclimate/dash-dv-explorer/actions/workflows/python-ci.yml/badge.svg)](https://github.com/pacificclimate/dash-dv-explorer/actions/workflows/python-ci.yml)

# Design Value Explorer

Plotly/Dash for interactive visualization of design value fields.

## Documentation

- [Installation](docs/installation.md)
- [Deployment for local development and for production](docs/deployment.md)
- [Testing](docs/testing.md)
- [Dev notes](docs/dev-notes.md)

## Changelog

For a summary of releases and changes, see [`NEWS.md`](NEWS.md).

## Releasing

To create a versioned release:

1. Increment `__version__` in `setup.py`
2. Summarize the changes from the last release in `NEWS.md`
3. Commit these changes, tag the release, then push it all:

  ```bash
git add setup.py NEWS.md
git commit -m"Bump to version x.x.x"
git tag -a -m"x.x.x" x.x.x
git push --follow-tags
  ```

## Authors

- Nic Annau, nannau@uvic.ca, Pacific Climate Impacts Consortium
- Rod Glover, rglover@uvic.ca, Pacific Climate Impacts Consortium
