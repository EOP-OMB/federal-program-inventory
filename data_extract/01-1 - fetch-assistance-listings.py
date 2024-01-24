import requests

# run an empty search on SAM.gov to get all IDs
r = requests.get('https://sam.gov/api/prod/sgs/v1/search/?index=cfda&page=0&mode=search&size=10000&is_active=true')

# extract the SAM.gov ID for each assistance listing from the search response
listing_ids = []
for listing in r.json()['_embedded']['results']:
    listing_ids.append(listing['_id'])

# fetch the JSON data for each assistance listing
listings_json_list = []
for listing_id in listing_ids:
    lr = requests.get('https://sam.gov/api/prod/fac/v1/programs/' + listing_id)
    listings_json_list.append(lr.text)

# save the JSON of the 
with open('source_files/assistance-listings.json', 'w') as file:
    file.write('['+','.join(listings_json_list)+']')