import json
import requests
import time
from string import ascii_lowercase

programs: set = set()
with open('source_files/assistance-listings.json') as f:
    assistance_listings_list = json.load(f)
    for l in assistance_listings_list:
        programs.add(str(l['data']['programNumber']))

# function to fetch the JSON data from USASpending.gov for each assistance listing
def query_usaspending_cfda(q):
    status_code = 000
    while status_code != 200:
        lr = requests.post('https://api.usaspending.gov/api/v2/autocomplete/cfda/', data={"search_text": q, "limit":10000})
        status_code = lr.status_code
        if status_code == 200:
            return lr.json()

# fetching by first letter allows us to significantly reduce the number of calls to USASpending.gov's API
listings_json: list = []
for c in ascii_lowercase:
    results = query_usaspending_cfda(c)
    if 'results' in results:
        for r in results["results"]:
            if r['program_number'] in programs:
                r['identifier'] = r['program_number'] # USASpending.gov's API requires this added attribute
                programs.discard(r['program_number'])
                listings_json.append(r)
                print("AL Count: " + str(len(listings_json)))

for p in programs:
    results = query_usaspending_cfda(p)
    if 'results' in results:
        for r in results["results"]:
            if r['program_number'] == p:
                r['identifier'] = r['program_number'] # USASpending.gov's API requires this added attribute
                programs.discard(r['program_number'])
                listings_json.append(r)
                print("AL Count: " + str(len(listings_json)))
            else:
                print("AL FAIL: " + p)

# fetch the hash for each program search results
i = 0
hashes: dict = {}
for l in listings_json:
    tries = 0
    status_code = 000

    # emulate the headers of USASpending.gov's frontend, to maximize the success rate when hitting the API
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/json',
        'X-Requested-With': 'USASpendingFrontend',
        'Origin': 'https://www.usaspending.gov',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Referer': 'https://www.usaspending.gov/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site'
    }

    # per USASpending.gov's API documentation, the below are required, even if empty
    obj = {
        "filters": {
            "keyword": {},
            "timePeriodType": "fy",
            "timePeriodFY": [],
            "timePeriodStart": None,
            "timePeriodEnd": None,
            "newAwardsOnly": False,
            "selectedLocations": {},
            "locationDomesticForeign": "all",
            "selectedFundingAgencies": {},
            "selectedAwardingAgencies": {},
            "selectedRecipients": [],
            "recipientDomesticForeign": "all",
            "recipientType": [],
            "selectedRecipientLocations": {},
            "awardType": [],
            "selectedAwardIDs": {},
            "awardAmounts": {},
            "selectedCFDA": {
                l['program_number']: l # inject the fetched program JSON
            },
            "naicsCodes": {
                "require": [],
                "exclude": [],
                "counts": []
            },
            "pscCodes": {
                "require": [],
                "exclude": [],
                "counts": []
            },
            "defCodes": {
                "require": [],
                "exclude": [],
                "counts": []
            },
            "pricingType": [],
            "setAside": [],
            "extentCompeted": [],
            "treasuryAccounts": {},
            "tasCodes": {
                "require": [],
                "exclude": [],
                "counts": []
            }
        },
        "version": "2020-06-01"
    }
    while status_code != 200 and tries < 5:
        tries += 1
        try:
            r = requests.post('https://api.usaspending.gov/api/v2/references/filter/', data=json.dumps(obj, separators=(',', ':')), headers=headers)
        except requests.exceptions.ConnectionError as e:
            print('Connection Error')
        status_code = r.status_code
        if status_code == 200:
            d = r.json()
            hashes[l['program_number']] = d['hash']
            i += 1
            print('Hashes: ' + str(i))
        else:
            time.sleep(tries)
            print('Hashes FAIL: {} {} {} {}'.format(str(status_code), str(tries), str(l['program_number']), json.dumps(obj, separators=(',', ':'))))

# save the JSON of the hashes to be used by later scripts
with open('source_files/usaspending-program-search-hashes.json', 'w') as file:
    file.write(json.dumps(hashes))