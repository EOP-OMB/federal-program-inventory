import json
import time
import requests

# produce a deduplicated list containing all assistance listing CFDA / program numbers
with open('source_files/assistance-listings.json') as f:
    assistance_listings_list = json.load(f)

assistance_listing_numbers = set()
for l in assistance_listings_list:
    assistance_listing_numbers.add(l['data']['programNumber'])

# USASpending.gov groups award types using the following breakdown (as of Aug. 30, 2023) and only allows for search on one group per query
award_type_groupings = [
        ["07", "08"], # loans
        ["02", "03", "04", "05"], # grants
        ["06", "10"], # other_financial_assistance
        ["09", "11"], # direct_payments
]

# query USASpending.gov's API to gather necessary data for each program
session = requests.Session()
for num in assistance_listing_numbers:
    awards = list()
    for group in award_type_groupings:
        current_page = 1
        next_page = True
        while next_page:
            d = {
                "subawards": False,
                "limit": 100,
                "page": current_page,
                "filters": {
                    "award_type_codes": group,
                    "time_period": [{"start_date": "2017-10-01", "end_date": "2023-08-30"}],
                    "program_numbers": [num]
                },
                "fields": [
                    "Award ID", # must be included first, or USASpending.gov will return a 500 error
                    "Award Amount",
                    "Award Type",
                    "Base Obligation Date",
                    "CFDA Number",
                    "Description",
                    "Place of Performance Country Code",
                    "Place of Performance State Code",
                    "COVID-19 Obligations",
                    "Infrastructure Obligations",
                    "recipient_id"
                ]
            }

            # USASpending.gov will occassionally terminate the connection unexpectedly; retry with backoff logic if / when this occurs
            retry = 0
            while retry < 50:
                try:
                    r = session.post('https://api.usaspending.gov/api/v2/search/spending_by_award/', json=d, timeout=5)
                except:
                    retry += 1
                    time.sleep(retry)
                else:
                    break

            try:
                j = r.json()
                if j['page_metadata']['hasNext']:
                    current_page+=1
                    if current_page > 99:
                        print(str(num))
                else:
                    next_page = False
                for result in j['results']:
                    awards.append(result)
            except:
                print('JSON Error: ' + str(num))
        
    with open('source_files/awards/' + str(num) + '.json', 'w') as file:
        file.write(json.dumps(awards))


"""
These programs had issues when being pulled via the script.
The plain numbers justs had too many awards to pull; the ones with error messages were malformed in some way.
Need to refactor to grab data for these programs, but everything else should be accurate.

84.007
45.024
10.113
84.268
59.075
10.130
59.008
64.039
64.100
10.123
64.127
64.105
32.004
10.410
93.859
59.073
10.069
59.078
10.964
47.070
14.267
59.012
10.148
10.427
14.157
14.181
10.112
10.056
10.976
64.117
47.049
10.108
19.040
32.008
57.001
10.109
64.124
10.912
10.920
10.127
10.924
10.132
20.205
10.447
97.022
10.131
14.871
10.116
JSON Error: 87.052
10.054
14.879
10.111
84.063
59.016
32.009
96.001
14.850
93.866
20.106
47.041
59.072
93.837
64.110
93.847
14.865
93.855
10.417
10.417
64.116
64.101
43.001
64.104
10.051
10.051
64.114
59.041
93.547
96.002
64.031
JSON Error: 66.616
10.133
64.032
84.358
32.005
10.110
64.106
93.853
84.033
97.044
84.425
47.050
14.872
10.139
64.109
14.183
10.171
14.195
14.117
10.451
98.001
JSON Error: 10.725
31.007
96.006
10.120
64.130
96.004
"""