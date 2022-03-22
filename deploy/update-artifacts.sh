#!/bin/bash
# Copy necessary items from repo to deployment directory. This is the changeable
# part of the deployment automation scripting. It changes as needed to accommodate
# changes to the project (e.g., new configuration files).
#
# This script is intended to be `source`d from `make-deploy.sh`, which defines
# variables `repo_dir`, `deploy_dir`
rm -rf "${deploy_dir:?}"/*
mkdir "${deploy_dir}"/docker
cp -r "${repo_dir}"/docker/production/ "${deploy_dir}"/docker
cp "${repo_dir}"/app-logging.yml "${deploy_dir}"
cp "${repo_dir}"/app-config.yml "${deploy_dir}"
cp -r "${repo_dir}"/config "${deploy_dir}"
