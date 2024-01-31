# Federal Program Inventory (FPI) website
The Federal Program Inventory is a website of the Office of Management & Budget (OMB), within the Executive Office of the President.

## How the Federal Program Investory built & hosted
The Federal Program Investory combines public data from several government websites to present a view of federal programs. This website is primarily focused on Federal Assistance Listings, and the feasibility of using those listings as the foundation for a larger Federal Program Investory.

The Federal Program Investory website is built with:

- [Jekyll](https://jekyllrb.com/) via the [github-pages gem](https://rubygems.org/gems/github-pages)
  - See [current dependencies](https://pages.github.com/versions/) for GitHub Pages
- [U.S. Web Design System v3 (USWDS)](https://designsystem.digital.gov/)

The FPI website is hosted on Github Pages, a fast and reliable static website host. For the production website, a custom domain of [fpi.omb.gov](https://fpi.omb.gov/) is used, with SSL enabled for all pages. These settings are configured in the Github repository settings.

Because of Github Pages limitations, some pre-processing is necessary prior to committing to Github Pages. Before getting started, make sure the following are installed on your system:

- [Python 3](https://www.python.org/)
- [Node.js](https://nodejs.org/) or [NPM](https://github.com/npm/cli)
- Docker (for ease, we recommend using a Docker-compatible container tool, such as [Podman](https://podman.io/) or [Docker Desktop](https://www.docker.com/))

## Install and run a development environment

### Initial setup
We recommmend that you use a Docker container to run the site as a development environment because of dependency and version collisions. This allows the site to run in a contained place, minimizing setup issues.

```
docker build -t fpi-website . --no-cache
```

### Run locally, with and without live reload
Run this command to have a local version on `http://localhost:4080`.
```
docker run -p 4080:4000  --name fpiweb fpi-website
```

If you want to make changes and have them update on the running container
we need to map the active source code in to the container with a volume mount and
expose the port for livereload. This should ensure that changes you make are being
mapped to the /app director and refresh on the running container. Note the volume mount syntax
for `pwd` might be different on Windows or a non Bash shell. 
```
docker run -p 4080:4000  -p 35729:35729 -v $(pwd):/app --name fpiweb fpi-website
```  

### Deploying to Github Pages
Deploying this site to Github Pages is a combination of local processes and Github Actions. To get started, you will need node.js 18.17.1 installed.

#### Compiling the CSS
If no updates have been made to the project CSS files or USDWS, this step may be skipped. However, if changes have been made, you must re-compile the

Once node.js is installed, install the necessary packages by running the following command from the root directory.
```
npm install
```

After the necessary packages have been installed, 

## Maintenance

### USWDS and custom styles
We use USWDS version 3. Most of the styles are built off of v2.12.0, but the underlying framework is v3. The `scss` is in `assets/stylesheets/uswds`, with the entry of `index.scss`. `uswds-settings.scss` has custom variables and `styles.scss` has custom scss.

#### Change theme settings

Custom USWDS theme settings are declared in `assets/stylesheets/uswds/_uswds-theme-*.scss`. Use these files to [add or remove utilities, edit variables, or change how the design system builds](https://designsystem.digital.gov/documentation/settings/).

After updating, make a [new build or restart your localhost](#running-and-building) to see any changes.

#### Updating USWDS
To update a major version of `uswds`, consult their documentation. The `package.json` settings will allow for minor and patch updates as a matter of course.