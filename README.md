![Docker Publishing](https://github.com/pacificclimate/dash-dv-explorer/workflows/Docker%20Publishing/badge.svg)
[![Python CI](https://github.com/pacificclimate/dash-dv-explorer/actions/workflows/python-ci.yml/badge.svg)](https://github.com/pacificclimate/dash-dv-explorer/actions/workflows/python-ci.yml)

# Design Value Explorer

Web application for visualizing and downloading design value fields and 
tables.

## Documentation

- [Installation](docs/installation.md)
- [Configuration](docs/configuration.md)
- [Deployment for local development](docs/deployment-dev.md)
- [Deployment for production](docs/deployment-prod.md)
- [Testing](docs/testing.md)
- [Dev notes](docs/dev-notes.md)

### *Note that the CI version of the tests is currently failing until this project goes through an upgrade cycle.*

## Changelog

For a summary of releases and changes, see [`NEWS.md`](NEWS.md).

## Releasing

To create a versioned release:

1. Increment `__version__` in `setup.py`
2. Summarize the changes from the last release in `NEWS.md`
3. IMPORTANT: Update the image tag in `docker/production/docker-compose.yml` to 
   the new version.
4. Commit these changes, tag the release, then push it all:

  ```bash
git add setup.py NEWS.md docker/production/docker-compose.yml
git commit -m"Bump to version x.x.x"
git tag -a -m"x.x.x" x.x.x
git push --follow-tags
  ```

## Authors

- Nic Annau, nannau@uvic.ca, Pacific Climate Impacts Consortium
- Rod Glover, rglover@uvic.ca, Pacific Climate Impacts Consortium
