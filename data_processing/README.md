# Federal Program Inventory Data Extraction

## About the data extraction
The data extraction contained in this directory pulls data from SAM.gov and USASpending.gov, for use in the Federal Program Inventory (FPI). The Federal Program Inventory is designed to make information about Federal programs, including program objectives and financial information, easier to access.

## Setting up your environment
Before getting started, you need to make sure that your system is set up properly. The data extract functionality is written in Python3 and has several dependencies. To set up your system:
1. Navigate to the root directory of this repository (one level above this directory), and establish a virtual environment using `python3 -m venv venv` (note that different environments may use different aliases for Python3; e.g., `python` versus `python3`)
2. Activate the virtual environment using `source venv/bin/activate`
3. Install dependencies using `pip install -r requirements.txt`

## Running the extract
> [!NOTE]
> This repository already contains copies of the latest data pulled by the FPI team. Unless you need to refresh the data, it is likely sufficient to use these pre-existing files and skip the extract below.

### SAM.gov
If you determine you need to extract the data from SAM.gov, ensure your system is set up and, with your virtual environment enabled, and return to this directory. To extract the necessary data from SAM.gov:

1. Run [01-1 - fetch-assistance-listings.py](01-1 - fetch-assistance-listings.py)
2. Run [01-2 - fetch-dictionary.py](01-2 - fetch-dictionary.py)
3. Run [01-3 - fetch-organizations.py](01-3 - fetch-organizations.py)
3. Run [01-4 - fetch-usaspending-hashes.py](01-4 - fetch-usaspending-hashes.py)

This process will generate four files in the [source_files](source_files) directory that contain the data necessary to generate the underlying FPI program pages. Note that this process will make several thousand calls to SAM.gov and USASpending.gov's APIs to retrieve the necessary data.

SAM.gov also publishes an annual PDF that is used in the FPI. The Functional Index from SAM.gov's annual PDF is extracted and used to generate the Categories and Sub-categories shown on the FPI website. Unfortunately, this information is not available from SAM.gov via API. The script used to extract these values is [00 - extract-functions-from-pdf.py](00 - extract-functions-from-pdf.py); however, future PDFs are likely to have different parameters and will need to be further customized.

### USASpending.gov
If you determine you need to extract the data from USASpending.gov, you must download and load significant amounts of data from USASpending.gov into a SQLite database. The intial download of this information may exceed 20GB compressed. Once uncompressed, the data and database may exceed 400GB.

The FPI uses USASpending.gov's monthly Award Data Archives that are [available for download](https://www.usaspending.gov/download_center/award_data_archive). To reduce the need to redownload the complete dataset monthly, USASpending.gov also makes monthly delta files available, which contain only the updates since the last month's release.



## Processing the data
> [!NOTE]
> This repository already contains copies of the latest data processed by the FPI team. Unless you need to refresh the data or want to perform your own analysis, it is likely sufficient to use these pre-existing files and skip the processing below.

The data from the SAM.gov and USASpending.gov extracts is processed into the Markdown files used by Jekyll to build the FPI website. To re-generate the Markdown files for Jekyll:
1. Run [02 - generate-category-subcategory-md.py](02 - generate-category-subcategory-md.py)
2. Run [02 - generate-programs-and-search-md.py](02 - generate-programs-and-search-md.py)

These two files could be combined in the future, but are currently separate due to how the development of the FPI website progressed.

## A note on extraction methods

### SAM.gov
The Assistance Listings data is extracted from SAM.gov via calls to their public-facing APIs. While SAM.gov also makes data publicly available for download in CSV format, using this data presented several issues:
1. **The data was not properly escaped.** When the data was downloaded from SAM.gov using their public export functionality, there were data quality issues caused by incorrect escaping of characters. This led to multiple fields running together, and a need for manual data review and cleaning whenever the underlying data for the FPI pilot was to be updated.
2. **The data was not designed to be easily usable.** The CSV available for public download was non-standard and its data was inconsistently encoded. For example, some columns contained nested JSON, whereas others contained delimited data with a variety of delimiters. SAM.gov does not publish a set of standards around the encoding of this data.
3. **The data set was incomplete.** The CSV available for public download did not contain the necessary data elements to support the FPI pilot. Critical fields, such as Assistance Usage were not available in the CSV.

Given these concerns with the downloadable CSV, the FPI team began exploring alternative methods of securing the necessary data. The most transparent and least impactful method identified was gathering the data using SAM.gov's public-facing APIs that are used to power their public website. While these APIs were not documented, the team was able to identify the necessary data values based on comparison to public website renderings and exact the necessary data. As SAM.gov does not make guarantees about these APIs, they may make breaking changes at any time.