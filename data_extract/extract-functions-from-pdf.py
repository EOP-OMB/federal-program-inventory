import pandas as pd
from tabula import read_pdf

# this process extracts the multiple columns of values on each page
# because of how the PDF is designed, this results in the headers
# being truncated; we merge in functions / sub-functions later in this
# script.

data_values = read_pdf(
    'source_files/2022-assistance-listing-catalog.pdf',
    output_format='dataframe',
    pandas_options={'header': None},
    pages=['151-208'],
    stream=True,
    multiple_tables=False,
    area=[[55, 60, 735, 90], [55,310,735,340]],
    encoding="utf-8"
)
data_values = data_values[0]

# remove a handful of outliers from page one that precede the template
# these are only valid for the 2022 PDF
data_values = data_values.drop(range(0,19))
data_values = data_values.drop(55).reset_index(drop=True)

# load in the 2022 functions list
functions_df = pd.read_csv('source_files/2022-functions-list.csv', header=None)

# loop through each of the values to assign the full function / sub-function
parent = '' # tracks the current function
child = '' # tracks the current sub-function
parent_col = []
child_col = []
remove_rows = []
all_subcategories = [] # tracks the rows to which "all subcategories" (aka sub-functions) apply
function_index = 0
data_index = 0
for row in data_values[0]:
    if data_index in [2110,2255]: # if row is one of two one-off two-line sub-functions; valid only for 2022 
        parent_col.append('')
        child_col.append('')
        remove_rows.append(data_index)
    elif row[0].isdigit(): # if row is a program number
        parent_col.append(parent)
        if child.startswith('All subcategories'):
            all_subcategories.append([row, parent])
            remove_rows.append(data_index)
        child_col.append(child)
    elif row.isupper(): # if row is a function
        parent_col.append('')
        child_col.append('')
        remove_rows.append(data_index)
    else: # if row is a sub-function
        r = functions_df.loc[function_index]
        function_index+=1
        parent = r[0]
        child = r[1]
        parent_col.append('')
        child_col.append('')
        remove_rows.append(data_index)
    data_index += 1

# create dict of functions / sub-functions
functions_dict = {}
for x in zip(functions_df[0], functions_df[1]):
    if x[0] not in functions_dict:
        functions_dict[x[0]] = []
    if not x[1].startswith('All subcategories'):
        functions_dict[x[0]].append(x[1])

# loop through those tagged as having all sub-functions apply and insert rows
new_vals = []
for val in all_subcategories:
    for subcat in functions_dict[val[1]]:
        new_vals.append(val[0])
        parent_col.append(val[1])
        child_col.append(subcat)

# append new columns to dataframe
data_values = pd.concat([data_values, pd.DataFrame(new_vals)], ignore_index=True)
data_values[1] = parent_col
data_values[2] = child_col

# drop the unnecessary rows and convert to csv
data_values = data_values.drop(remove_rows).reset_index(drop=True).to_csv('data_extracts/db_program_to_function_sub_function.csv', index=False, header=False)