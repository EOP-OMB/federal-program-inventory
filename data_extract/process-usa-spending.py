import json
import os
from datetime import date
import pandas as pd

pd.set_option('display.max_columns', None)

# loop through individual program files to create a dictionary of all awards
awards = []
dir = 'source_files/awards/'
for file in os.listdir(dir):
    filename = os.fsdecode(file)
    if filename.endswith(".json"):
        with open(dir + filename) as f:
            for l in json.loads(f.read()):
                awards.append(l)

# load the dictionary into a pandas dataframe
awards_df = pd.DataFrame.from_dict(awards)

# add a column containing fiscal year
col_fiscal_year = []
for d in awards_df['Base Obligation Date']:
    date_obj = date.fromisoformat(d)
    fiscal_year = date_obj.year # convert date to FY
    if date_obj.month > 9:
        fiscal_year += 1
    col_fiscal_year.append(fiscal_year)
awards_df['Fiscal Year'] = col_fiscal_year

# generate CSV containing summarized dats
awards_df.groupby(['CFDA Number', 'Fiscal Year', 'Place of Performance Country Code', 'Place of Performance State Code', 'Award Type']) \
         .agg({'COVID-19 Obligations': 'sum', 'Infrastructure Obligations': 'sum', 'Award Amount': 'sum'}) \
         .reset_index().to_csv('data_extracts/db_program_to_award_summary.csv', index=False)