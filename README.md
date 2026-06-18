# Federal Program Inventory

## About the inventory
The [Federal Program Inventory (FPI)](https://fpi.omb.gov/) is a comprehensive, searchable tool with critical information about all Federal programs that provide grants, loans, or direct payments to individuals, governments, firms or other organizations. The FPI increases government transparency and accessibility and fulfills Congressional mandates to the Office of Management and Budget (OMB) to create and publicly post an inventory.

## About the repository
This repository contains four main sub-directories: (1) [api](api), which contains code for the API that exposes the FPI's elasticsearch instance; (2) [data_processing](data_processing), which contains code for the extract, transform, and load process that gathers and processes the underlying data for the FPI; (3) [indexer](indexer), which contains code to add programs to the FPI's elasticsearch index upon launch; and (4) [website](website), which contains code to build the public-facing FPI website. See the README.md files in each of these directories for more information.

## The build process
The various images that are deployed to run the FPI are generated using Github Actions. The scripts to do so are found in the [.github/workflows](.github/workflows) sub-directory. Github Actions will build three images (website, api, and indexer) upon commit to any of the `[stage]-release` branches. Deployment of these images must then be manually triggered / confirmed on internal systems to deploy the images to the respective environments.
