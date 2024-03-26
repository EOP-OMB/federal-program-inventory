# Federal Program Inventory (FPI) website

## Building the website
The FPI website is generated using data from SAM.gov and USASpending.gov. This repository contains all of the information used to build the current FPI website.

The website is built using [Jekyll](https://github.com/jekyll/jekyll), a widely-used open-source static site generator, as well as the [U.S. Web Design System](https://github.com/uswds/uswds). The site is generated inside of an isolated Docker container. This container builds the website using Jekyll and packages the resulting files into an [nginx-unprivileged](https://github.com/nginxinc/docker-nginx-unprivileged) image for deployment.

To run the website locally (available on port 4000):

1. Navigate to `/website/`
2. Run `docker build -t fpi-website .`
3. Run `docker run -p 4000:8080 --name fpiweb fpi-website`

## Data extraction
To learn more about the data that powers the FPI website and how to update it, navigate to the [data_extraction](data_extract/README.md) sub-directory.

## Deploying the website

### Github Actions
When a new commit is made to the `release` branch, Github Actions will automatically trigger a build of the website using the process described above. Once completed, this will create a new deployable package on Github Packages.