import requests
import shutil
import time

suffix_date = "20251206"
sleep_seconds = 30
# check https://www.usaspending.gov/download_center/award_data_archive for available years
# the range should be first year available to last year available + 1
for year in range(2025, 2026):
    url = f"https://files.usaspending.gov/award_data_archive/FY{year}_All_Assistance_Full_{suffix_date}.zip"
    filename = f"FY{year}_All_Assistance_Full_{suffix_date}.zip"

    try:
        # Use stream=True to handle large files efficiently without loading the whole file into memory
        with requests.get(url, stream=True) as response:
            print(f"Downloading {url} ...")
            response.raise_for_status() # Raise an exception for bad status codes (4XX or 5XX)
            with open(filename, 'wb') as out_file:
                shutil.copyfileobj(response.raw, out_file)
        print(f"Successfully downloaded '{filename}'")
        print(f"Sleeping for {sleep_seconds} seconds...")
        time.sleep(sleep_seconds)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")