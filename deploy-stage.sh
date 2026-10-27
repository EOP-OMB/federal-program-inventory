#!/usr/bin/env bash

set -euo pipefail

if [[ -n "$(git status --porcelain --untracked-files=all -- . ':(top,exclude)deploy-stage.sh')" ]]; then
  echo "Working tree is not pristine. Please stash or commit your changes before deploying staging." >&2
  exit 1
fi

git checkout stag-release
git pull

git checkout prod-release
git pull

temp_branch="temp-resolve-$(date +%s)"
git checkout -b "$temp_branch"

# Start a merge so the resulting commit records stag-release as a parent.
# Any conflicts are resolved by replacing the complete tracked tree below.
if ! git merge --no-commit --no-ff -X theirs stag-release; then
  if [[ ! -f "$(git rev-parse --git-path MERGE_HEAD)" ]]; then
    echo "Unable to merge stag-release." >&2
    exit 1
  fi
fi

# Make both the index and working tree exactly match stag-release. This also
# removes tracked files that do not exist on stag-release.
git read-tree --reset -u stag-release

git commit --allow-empty -m "synced stag-release for staging deployment"

git push -u origin "$temp_branch"