import json
import requests

# run an empty search on SAM.gov to get all IDs
r = requests.get('https://sam.gov/api/prod/sgs/v1/search/?index=cfda&page=0&mode=search&size=10000&is_active=true')

# extract the organization IDs for each assistance listing from the search response
organization_ids_set = set()
for listing in r.json()['_embedded']['results']:
    if listing.get('organizationHierarchy'):
        for organization in listing['organizationHierarchy']:
            organization_ids_set.add(organization['organizationId'])

# fetch the JSON data for each organization
organizations_json_list = []
for organization_id in organization_ids_set:
    lr = requests.get('https://sam.gov/api/prod/federalorganizations/v1/organizations/' + organization_id)
    org = lr.json()
    organizations_json_list.append(json.dumps(org['_embedded'][0]['org']))

# save the JSON of the 
with open('source_files/organizations.json', 'w') as file:
    file.write('['+','.join(organizations_json_list)+']')