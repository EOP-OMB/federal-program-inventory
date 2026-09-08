import json
import os

output_file = 'sam_summary_file.csv'
summary = {}
with open(os.path.join('..','extracted','assistance-listings.json'), 'r') as file:
    data = json.load(file)
    for item in data:
        summary[item['data']['programNumber']] = []
        if 'financial' in item['data'] and 'obligations' in item['data']['financial']:
            for obligation_line in item['data']['financial']['obligations']:
                if 'values' in obligation_line:
                    for obligation_item in obligation_line['values']:
                        if 'actual' in obligation_item or 'estimate' in obligation_item:
                            actual = 0
                            if 'actual' in obligation_item:
                                actual = obligation_item['actual']
                            estimate = 0
                            if 'estimate' in obligation_item:
                                estimate = obligation_item['estimate']
                            summary[item['data']['programNumber']].append({
                                'actual': actual,
                                'estimate': estimate,
                                'year': obligation_item['year']
                            })

# save to csv
lines = ["aln,year,actual,estimate"]
for aln, years in summary.items():
    for year in years:
        lines.append(f"{aln},{year['year']},{year['actual']},{year['estimate']}")
with open(output_file, 'w') as file:
    print('Saving file ...')
    file.write('\n'.join(lines))
    print(f"File {output_file} saved successfully.")