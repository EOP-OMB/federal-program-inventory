import csv
import io
import zipfile

suffix_date = "20251206"
output_file = "usaspending_summary_file.csv"
    
def read_csv_from_zip_in_memory(zip_filename):
    summary_data = {}

    # Open the zip file in read mode ('r')
    with zipfile.ZipFile(zip_filename, 'r') as zipf:
        for filename in zipf.namelist():
            # Open the specific CSV file within the zip archive
            # zipf.open() returns a binary file-like object
            with zipf.open(filename, 'r') as f:
                # Wrap the binary stream with io.TextIOWrapper for text decoding
                # Specify the correct encoding (utf-8 is common) and newline=''
                text_wrapper = io.TextIOWrapper(f, encoding='utf-8', newline='')
                
                # Pass the text wrapper to csv.DictReader
                reader = csv.DictReader(text_wrapper)
                
                # Iterate over the rows
                for row in reader:
                    # Each row is a dictionary (OrderedDict in older Python versions)
                    if (row['cfda_number'] not in summary_data):
                        summary_data[row['cfda_number']] = {
                            'obligations': 0,
                            'outlays': 0
                        }

                    if row['federal_action_obligation'] != '':
                        summary_data[row['cfda_number']]['obligations'] += float(row['federal_action_obligation'])

                    if row['total_outlayed_amount_for_overall_award'] != '':
                        summary_data[row['cfda_number']]['outlays'] += float(row['total_outlayed_amount_for_overall_award'])
    return summary_data

def summary_data_to_csv(year, summary_data):
    lines = []
    for cfda, spending_data in summary_data.items():
        lines.append(f"{cfda},{year},{spending_data['obligations']},{spending_data['outlays']}")
    return lines

csv_lines = ["cfda,year,obligations,outlays"]
for year in range(2008,2027):
    filename = f"FY{year}_All_Assistance_Full_{suffix_date}"
    print(f"Reading file {filename} ...")
    summary_data = read_csv_from_zip_in_memory(filename + '.zip')
    csv_lines += summary_data_to_csv(year, summary_data)

with open(output_file, 'w') as file:
    print('Saving file ...')
    file.write('\n'.join(csv_lines))
    print(f"File {output_file} saved successfully.")