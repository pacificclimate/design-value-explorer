#!/bin/bash -x
# make-deploy assumes the following and *only* the following about the
# directories and files it is run from:
#
#   <deployment base dir>/      # e.g., /storage/data/projects/design-value-explorer
#     dev/                      # development deployments
#     prod/                     # production deployments
#     repo/                     # clone of project repo
#       deploy/                 # contains deployment support scripts
#         make-deploy.sh        # unchanging(*) support script
#         ...                   # other scripts or files it may need (changeable)
#
# (*) Read "unchanging" with a grain of salt. You may have to update the repo from
# time to time if this script changes, but it is intended to capture the slowly-
# changing part of this procedure. The "other scripts or files" capture the
# more volatile changes (such as what artifacts need to be copied).

script_dir="$(dirname ${BASH_SOURCE[0]})"
repo_dir="$(cd $script_dir/..; pwd)"
base_dir="$(cd $script_dir/../..; pwd)"

echo "script_dir=$script_dir"
echo "repo_dir=$repo_dir"
echo "base_dir=$base_dir"

mode=$1
if ! echo "$mode" | grep -E -q '(dev|prod)'; then
  echo "First argument must be 'dev' or 'prod'; received '$mode'"
  exit 1
fi

tag=$2
if [ -z "$tag" ]; then
  echo "Second argument required. Must be a commit name (branch, tag, sha)."
  exit 1
fi

deploy_dir="$mode/$tag"

# Update the repo to the latest version of the specified branch.
if ! cd "$repo_dir"; then
  # This can't happen given that this script is in repo. But ...
  echo "Error: Project repo is missing. Please clone project into '$repo_dir'"
  exit 1
fi
if ! git fetch origin "$tag"; then
  echo "Error: Ref '$tag' does not exist in project repo."
  exit 1
fi
git checkout "$tag"
cd ..

# Create the new deployment directory
echo "Creating $deploy_dir"
mkdir -p "$deploy_dir"

# Conditionally update the deployment artifacts
doit=""
while [[ $doit == "" || $doit =~ y|Y ]]; do
  read -n1 -p "Update deployment artifacts? [y,n] " doit
  case $doit in
    y|Y) echo; \
          ls $script_dir;
          source "$script_dir/update-artifacts.sh"; \
          break;;
    n|N) break;;
    *) echo "Please enter y or n";;
  esac
done
