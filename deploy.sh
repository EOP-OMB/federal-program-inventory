#!/bin/bash

# to use:
# 1. fork https://github.com/EOP-OMB/federal-program-inventory
# 2. clone the forked repo to ~/source/federal-program-inventory/ (or change the directory in this script)
# 3. create the temp directory ~/tmp (or change this script) 
# 4. run the script
# 5. push the changes to the forked repo, branch main
# 6. create a PR to https://github.com/EOP-OMB/federal-program-inventory branch main
# 7. promote through branches test-release, stag-release, prod-release 
clear
cd ~/source/federal-program-inventory/
if [[ `git status --porcelain` ]]; then
  echo "git status --porcelain is not empty"
  exit 1
fi
git checkout main
git pull

cd ~
rm -rf ~/tmp/federal-program-inventory/
rm -rf ~/tmp/omb-fpi/
mkdir -p ~/tmp
mkdir -p ~/tmp/federal-program-inventory
mkdir -p ~/tmp/federal-program-inventory/indexer
mkdir -p ~/tmp/federal-program-inventory/website

# files that differ between BAH and public
mv ~/source/federal-program-inventory/.git ~/tmp/federal-program-inventory/.git
mv ~/source/federal-program-inventory/.github ~/tmp/federal-program-inventory/.github
mv ~/source/federal-program-inventory/indexer/index_programs.py ~/tmp/federal-program-inventory/indexer/index_programs.py
mv ~/source/federal-program-inventory/docker-compose.yml ~/tmp/federal-program-inventory/docker-compose.yml
mv ~/source/federal-program-inventory/website/Dockerfile ~/tmp/federal-program-inventory/website/Dockerfile
mv ~/source/federal-program-inventory/website/nginx.conf ~/tmp/federal-program-inventory/website/nginx.conf

# replace files
rm -rf ~/source/federal-program-inventory/*
cd tmp
git clone -b dev git@github.boozallencsn.com:oea-digital-support/omb-fpi.git
cp -a ~/tmp/omb-fpi/. ~/source/federal-program-inventory/

# fix files that differ
rm -rf ~/source/federal-program-inventory/.git
mv ~/tmp/federal-program-inventory/.git ~/source/federal-program-inventory/.git
rm -rf ~/source/federal-program-inventory/.github
mv ~/tmp/federal-program-inventory/.github ~/source/federal-program-inventory/.github
rm -rf ~/source/federal-program-inventory/indexer/index_programs.py
mv ~/tmp/federal-program-inventory/indexer/index_programs.py ~/source/federal-program-inventory/indexer/index_programs.py
rm -rf ~/source/federal-program-inventory/docker-compose.yml
mv ~/tmp/federal-program-inventory/docker-compose.yml ~/source/federal-program-inventory/docker-compose.yml
rm -rf ~/source/federal-program-inventory/website/Dockerfile
mv ~/tmp/federal-program-inventory/website/Dockerfile ~/source/federal-program-inventory/website/Dockerfile
rm -rf ~/source/federal-program-inventory/website/nginx.conf
mv ~/tmp/federal-program-inventory/website/nginx.conf ~/source/federal-program-inventory/website/nginx.conf

# remove unnecessary files / directories
rm -rf ~/source/federal-program-inventory/push-fpi.sh

# clear tmp
rm -rf ~/tmp/federal-program-inventory/
rm -rf ~/tmp/omb-fpi/

cd ~/source/federal-program-inventory/
git status
echo "Review the repo, make a commit, and push when ready"