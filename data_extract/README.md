# Federal Program Inventory Pilot Data Extraction

> [!WARNING]
> This repository and README are still under active development and have not yet reached release stage.

## About the data extraction
The data extaction contained in this directory pulls data from SAM.gov and USASpending.gov, for use in the Federal Program Invetory (FPI) pilot. This pilot is designed to explore whether Assistance Listings data from SAM.gov is appropriate to use as a foundation for 

## Setting up your environment
Before getting started, you need to make sure that your system is setup properly. The data extract functionality is written in Python3 and has a number of dependencies. To setup your system:
1. Navigate to the root directory of this repository (one level above this directory), and establish a virtual environment using `python3 -m venv venv` (note that different environments may use different aliases for Python3; e.g., `python` versus `python3`)
2. Activate the virtual environment using `source venv/bin/activate`
3. Install dependencies using `pip install -r requirements.txt`

## Running the extact
> [!NOTE]
> This repository already contains copies of the latest data pulled by the FPI team. Unless you need to refresh the data, it is likely sufficient to use these pre-existing files and skip the extract below.

### SAM.gov
If you determine you need to extract the data from SAM.gov, ensure your system is setup, with your virtual environment enabled, and return to this directory. To extract the necessary data from SAM.gov:

1. Run `fetch-assistance-listings.py`
2. Run `fetch-dictionary.py`
3. Run `fetch-organizations.py`

This process will generate three files in the `source_files` directory that contain the data necessary to generate the underlying FPI summary data. Note that this process will make several thousand calls to SAM.gov's APIs to retrive the data.

### USASpending.gov
> [!NOTE]
> USASpending.gov makes available a number of public-facing APIs to retrive data. They also make available a complete export of their database.
>
> Both methods of retriving the data come with significant disadvantages. For the API, retriving the necessary information takes hundreds of thousands of API calls. For the database, the size of the database is over 1TB and takes hours to restore.
>
> The FPI pilot team is exploring both options. Below is the information on API-based extraction. Note that, even on a powerful machine with high-speed internet, this process takes many hours to complete.

If you would like to extract the data from USASpending.gov, ensure your system is setup, with your virtual environment enabled. From this directory:

1. Run `fetch-usa-spending.py`

This process will generate one file per program in the `source_files/awards` directory, containing the necessary data in JSON format. Note that this process will make several hundred thousand calls to USASpending.gov's APIs to retrive the data, as many calls are required per program.

The FPI pilot team is exploring database-driven solutions to securing this data and will update this repository to reflect replication steps and related scripts, as appropriate.

## Processing the data
> [!NOTE]
> This repository already contains copies of the latest data processed by the FPI team. Unless you need to refresh the data or want to perform your own analysis, it is likely sufficient to use these pre-existing files and skip the processing below.
The data from the SAM.gov and USASpending.gov extracts is processed into flattened, purposed-built, relational CSVs. These CSVs are intended to be imported into PowerBI for analysis by the FPI pilot team. In future iterations of this project, data will be extracted to power the visualizations and data tables on the FPI pilot website.

### SAM.gov
Processing for the SAM.gov data is currently held in a Jupyter Notebook (`process-sam.ipynb`). To access this file using the Jupyter Notebook interface, run `jupyter notebook` from your virtual environment.

The stages in the Jupyter Notebook are largely leftover from some initial analysis. As a result, it performs some unnecessary computation in the process of producing the flattened CSVs. To produce updated CSVs, perform the steps in the Jupyter Notebook from top-to-bottom. This will produce a number of related, summary CSVs suitable for analysis. The FPI pilot team may update this file in the future to further streamline the process.

### USASpending.gov
Processing for the USASpending.gov data is held in `process-usa-spending.py`. To process the USASpending.gov data, run this file. It will produce a flattened CSV with summary award data for each program.

## A note on extraction methods

### SAM.gov
The Assistance Listings data is extacted from SAM.gov using a variety of calls to public-facing APIs. While SAM.gov makes data publicly available for download in CSV format, use of this data had several issues:
1. **The data was not properly escaped.** When the data was downloaded from SAM.gov using their public export functionality, there were data quality issues caused by incorrect escaping of characters. This led to multiple fields running together, and a need for manual data review and cleaning whenever the underlying data for the FPI pilot was to be updated.
2. **The data was not designed to be easily usable.** The CSV available for public download was non-standard and inconsistent on how it encoded data. For example, some columns contained nested JSON, whereas others contained delimited data with a variety of delimiters. SAM.gov does not publish a set of standards around the enconding of this data.
3. **The data set was incomplete.** The CSV available for public download did not contain the necessary data elements to support the FPI pilot. Critical fields, such as Assistance Usage were not available in the CSV.

Given these concerns with the downloadable CSV, the FPI pilot team began exploring alternative methods of securing the necessary data. The most transparent and least impactful method identified was gathering the data using SAM.gov's public-facing APIs that are used to power their public website. While these APIs were not documented, the team was able to identify the necessary data values based on comparison to public website renderings and exact the necessary data.