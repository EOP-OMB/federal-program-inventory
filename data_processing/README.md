# Federal Program Inventory Data Extract, Transform, and Load Process

## About the process
The data extract, transform, and load process contained in this directory pulls data from SAM.gov, USASpending.gov, and other sources for use in the Federal Program Inventory (FPI). The FPI is designed to make information about Federal programs, including program objectives, results, and financial information, easier to access.

## Setting up your environment
Before getting started, you need to make sure that your system is set up properly. The data extract functionality is written in Python3 and has several dependencies. To set up your system:
1. Navigate to the root directory of this repository (one level above this directory), and establish a virtual environment using `python3 -m venv venv` (note that different environments may use different aliases for Python3; e.g., `python` versus `python3`)
2. Activate the virtual environment using `source venv/bin/activate`
3. Install dependencies using `pip install -r requirements.txt`

## Running the extract
> [!NOTE]
> This repository already contains copies of the latest data pulled by the FPI team. Unless you need to refresh the data, it is likely sufficient to use these pre-existing files and skip the extract steps below.

### SAM.gov
Assistance Listing data can be updated at any time by agencies. However, updates occur most commonly in the fall, following OMB's data call to agencies. This update should be performed at least once per year. To extract the data from SAM.gov, ensure your system is set up and, with your virtual environment enabled, and return to this directory. You should uncomment the appropriate functions in [extract.py](extract.py) and then execute the script. Relevant functions include:
1. `extract_assistance_listing()`: downloads all Assistance Listings from SAM.gov using the API that powers their frontend (this approach is necessary, as their publicly documented APIs and data extracts do not provide usable data), and saves the result to [extracted/assistance_listings.json](extracted/assistance_listings.json)
2. `extract_dictionary()`: downloads the various enum lookup values that are referenced in the extracted Assistance Listing data, and saves the result to [extracted/dictionary.json](extracted/dictionary.json); this should generally be run whenever `extract_assistance_listing()` is run
3. `extract_organizations()`: downloads the organization lookup values that are referenced in the extracted Assistance Listing data, and saves the result to [extracted/organizations.json](extracted/organizations.json); this should generally be run whenever `extract_assistance_listing()` is run 
4. `clean_all_data()`: fixes some idiocracies in the [extracted/assistance_listings.json](extracted/assistance_listings.json) file, which result from bad data SAM.gov data
5. `extract_usaspending_award_hashes()`: runs searches against USASpending.gov for each Assistance Listing to generate the unique hash associated with the search results (this hash is subsequently used to generate a link on the Program page), and saves the result to [usaspending-program-search-hashes.json](usaspending-program-search-hashes.json); this should generally be run whenever `extract_assistance_listing()` is run 

Running the above fundtions process will generate four files in the [extracted](extracted) directory that contain some of the data necessary to generate the underlying FPI program pages. Note that this process will make several thousand calls to SAM.gov and USASpending.gov's APIs to retrieve the necessary data. The latest copies of this data are commited to this repo to minimize the need to run these functions.

SAM.gov also publishes an annual PDF that is used in the FPI. The Functional Index from SAM.gov's annual PDF is extracted and used to generate the Categories and Sub-categories shown on the FPI website. Unfortunately, this information is not available from SAM.gov via API. The function in [extract.py](extract.py) used to extract these values is `extract_categories_from_pdf()`. Annually, the new PDF should be downloaded from SAM.gov and the Categories and Sub-categories should be re-extracted. Note that future PDFs are likely to have slightly different layouts and parameters, which will require tweaks to this function.

### USASpending.gov
If you determine you need to extract the data from USASpending.gov, you must download and load significant amounts of data from USASpending.gov into a SQLite database. The intial download of this information may exceed 20GB compressed. Once uncompressed, the data and database may exceed 400GB. This information should be refreshed at least annually, but may be refreshed as freqeuntly as monthly.

The FPI uses USASpending.gov's monthly Award Data Archives that are [available for download](https://www.usaspending.gov/download_center/award_data_archive). To reduce the need to redownload the complete dataset monthly, USASpending.gov also makes monthly delta files available, which contain only the updates since the last month's release.

To load this data iniatially, you should download the "Financial Assistance" data, for current year and each of the six years prior, via the link above. This should result in seven archives. The names of these archives should generally look like `FY2024_All_Contracts_Full_20250406.zip`. Note the `Full` in this file name--for the initial load, you should download the `Full` archives for each year.

Once the files have been downloaded, recursively extract the archives and place all of the resulting CSV files into a single directory. This directory can then be used to run `load_usaspending_initial_files()` and `transform_and_insert_usaspending_aggregation_data()` in [transform.py](transform.py). These functions will load the CSVs into a SQLite DB, query that DB to extract summary tables, and then insert those summary tables into the [transformed/transformed_data.db](transformed/transformed_data.db) SQLite DB.

USASpending.gov releases updates monthly. Once the initial data is loaded onto your local machine, you can apply the monthly "Delta" files to your existing USASpending SQLite DB (not stored in this repo), rather than repeating this entire process. To do so, download the monthly "Delta" file at the same link about (rather than the "Full" file), and run `load_usaspending_delta_files()` and `transform_and_insert_usaspending_aggregation_data()` in [transform.py](transform.py) instead.

While this process may not appear optimal at face value, it is designed to: (1) work within the constraints of Government technology; (2) minimize the amount of data that must be downloaded (via Dalta files); and (3) result in a collection of summary tables that can be committed to this repo, for auditability and ease-of-startup for new team members and members of the public (by not requiring the download of any USASpending.gov data to build the website).

### Additional data
The FPI also uses additional data, which is sourced from several locations and should be refreshed on varying schedules. These include:
1. [extracted/additional-programs.csv](extracted/additional-programs.csv): this contains additional programs beyond Assistance Listings, including Interest on the Public Debt ([source](https://www.usaspending.gov/explorer/), All Budget Functions > Net Interest > Interest on Treasury Debt Securities > Interest on the Public Debt > switch to table mode) and Tax Expenditures ([source](https://home.treasury.gov/policy-issues/tax-policy/tax-expenditures), tab "Table 1 - Totals"); these should be refreshed at  annually (a manual process)
2. [extracted/improper-payment-program-mapping.csv](extracted/improper-payment-program-mapping.csv): this contains a mapping between programs in the FPI and programs reported on [PaymentAccuracy.gov](https://paymentaccuracy.gov/), as reported by agencies via an OMB data call; this should be refreshed at least annually (a manual process)
3. The following are sent by the OMB team annually for taxonomy updates:
  1. [extracted/FPI_GWO_assignment.csv](extracted/FPI_GWO_assignment.csv)
  2. [extracted/FPI_PON_assignment.csv](extracted/FPI_PON_assignment.csv)
  3. [extracted/Taxonomy_GWO_crosswalk.csv](extracted/Taxonomy_GWO_crosswalk.csv)
  4. [extracted/Taxonomy_PON_crosswalk.csv](extracted/Taxonomy_PON_crosswalk.csv)

## Transforming the data
> [!NOTE]
> This repository already contains copies of the latest data transformed by the FPI team. Unless you need to refresh the data or want to perform your own analysis, it is likely sufficient to use the pre-existing [transformed/transformed_data.db](transformed/transformed_data.db) file and skip the process below.

The data extracted above is transformed through a variety of processes into a SQLite DB ([transformed/transformed_data.db](transformed/transformed_data.db)). If new data was extracted by running functions in [extract.py](extract.py), the functions in [transform.py](transform.py) should be run to refresh [transformed/transformed_data.db](transformed/transformed_data.db). This SQLite DB is used in the next step, to generate the Markdown files used by Jekell to build the FPI website.

## Loading the data
> [!NOTE]
> This repository already contains copies of the latest data loaded by the FPI team. Unless you refreshed the data, it is likely sufficient to use the pre-existing markdown files located in [/website](/website) generated by this process.

To regenerate the Markdown files used by Jekell to build the website, uncomment the relevant functions at the bottom of [load.py](load.py) and run this file.

## A note on extraction methods

### SAM.gov
The Assistance Listings data is extracted from SAM.gov via calls to their public-facing APIs. While SAM.gov also makes data publicly available for download in CSV format, using this data presented several issues:
1. **The data was not properly escaped.** When the data was downloaded from SAM.gov using their public export functionality, there were data quality issues caused by incorrect escaping of characters. This led to multiple fields running together, and a need for manual data review and cleaning whenever the underlying data for the FPI pilot was to be updated.
2. **The data was not designed to be easily usable.** The CSV available for public download was non-standard and its data was inconsistently encoded. For example, some columns contained nested JSON, whereas others contained delimited data with a variety of delimiters. SAM.gov does not publish a set of standards around the encoding of this data.
3. **The data set was incomplete.** The CSV available for public download did not contain the necessary data elements to support the FPI pilot. Critical fields, such as Assistance Usage were not available in the CSV.

Given these concerns with the downloadable CSV, the FPI team began exploring alternative methods of securing the necessary data. The most transparent and least impactful method identified was gathering the data using SAM.gov's public-facing APIs that are used to power their public website. While these APIs were not documented, the team was able to identify the necessary data values based on comparison to public website renderings and exact the necessary data. As SAM.gov does not make guarantees about these APIs, they may make breaking changes at any time.
