# Federal Program Inventory Pilot Data Extraction

> [!WARNING]
> **This repository and README are still under active development and have not yet reached release stage.**

## About the data extraction
The data extaction contained in this directory pulls data from SAM.gov and USASpending.gov, for use in the Federal Program Invetory (FPI) pilot. This pilot is designed to explore whether Assistance Listings data from SAM.gov is appropriate to use as a foundation for 

## Running the extact
To extract the necessary data from SAM.gov:
1. Run `fetch-assistance-listings.py`
2. Run `fetch-dictionary.py`
3. Run `fetch-organizations.py`

This process will generate three files in the `source_files` directory that contain the data necessary to generate the underlying FPI summary data.

## Extraction methods

### SAM.gov
The Assistance Listings data is extacted from SAM.gov using a variety of calls to public-facing APIs. While SAM.gov makes data publicly available for download in CSV format, use of this data had several issues:
1. **The data was not properly escaped.** When the data was downloaded from SAM.gov using their public export functionality, there were data quality issues caused by incorrect escaping of characters. This led to multiple fields running together, and a need for manual data review and cleaning whenever the underlying data for the FPI pilot was to be updated.
2. **The data was not designed to be easily usable.** The CSV available for public download was non-standard and inconsistent on how it encoded data. For example, some columns contained nested JSON, whereas others contained delimited data with a variety of delimiters. SAM.gov does not publish a set of standards around the enconding of this data.
3. **The data set was incomplete.** The CSV available for public download did not contain the necessary data elements to support the FPI pilot. Critical fields, such as Assistance Usage were not available in the CSV.

Given these concerns with the downloadable CSV, the FPI pilot team began exploring alternative methods of securing the necessary data. The most transparent and least impactful method identified was gathering the data using SAM.gov's public-facing APIs that are used to power their public website. While these APIs were not documented, the team was able to identify the necessary data values based on comparison to public website renderings and exact the necessary data.

### USASpending.gov