import csv
import json
import yaml
from decimal import Decimal

with open('source_files/assistance-listings.json') as f:
    assistance_listings_list = json.load(f)

with open('source_files/dictionary.json') as f:
    dictionary_list = json.load(f)
    
with open('source_files/organizations.json') as f:
    organizations_list = json.load(f)

# load dictionary values into dataframe
for i in dictionary_list['_embedded']['jSONObjectList']:
    if i['id'] == 'assistance_type':
        assistance_types = {}
        for e in i['elements']:
            for s in e['elements']:
                assistance_types[s['element_id']] = s['value']
    if i['id'] == 'applicant_types':
        applicant_types = {}
        for e in i['elements']:
            applicant_types[e['element_id']] = e['value']
    if i['id'] == 'beneficiary_types':
        beneficiary_types = {}
        for e in i['elements']:
            beneficiary_types[e['element_id']] = e['value']

# load organization data
org_names = {}
for o in organizations_list:
    org_names[o['orgKey']] = o.get('agencyName', o.get('name', ''))
org_list = {}
for o in organizations_list:
    org_list[o['orgKey']] = {
        'agency': org_names.get(o.get('l1OrgKey'), ''),
        'sub-agency': org_names.get(o.get('l2OrgKey'), '')
    }
organizations_list = org_list

# load category data
data = {}
with open('source_files/2022-program-to-function-sub-function.csv', newline='') as f:
    r = csv.reader(f)
    for row in r:
        if not data.get(row[0]):
            data[row[0]] = set()
        data[row[0]].add((row[1], row[2]))
category_list = {}
for k in data:
    category_list[k] = []
    for v in data[k]:
        category_list[k].append(v[0]+' - '+v[1])

# define the relevant years for spending data
spending_years = ['2019', '2020', '2021', '2022', '2023']

# load SAM.gov financial obligations
sam_spending = {}
for l in assistance_listings_list:
    if l['data']['programNumber'] not in sam_spending:
        sam_spending[l['data']['programNumber']] = {}
        for y in spending_years:
            sam_spending[l['data']['programNumber']][y] = {
                'estimate': Decimal(0),
                'actual': Decimal(0)
            }
    for o in l['data']['financial']['obligations']:
        for row in o.get('values', []):
            if str(row['year']) in spending_years:
                if row.get('actual'):
                    sam_spending[l['data']['programNumber']][str(row['year'])]['actual'] += Decimal(row['actual'])
                if row.get('estimate'):
                    sam_spending[l['data']['programNumber']][str(row['year'])]['estimate'] += Decimal(row['estimate'])

# load USASpending.gov obligations data
usa_spending = {}
with open('source_files/usaspending_db_obligations_by_program.csv', newline='') as f:
    r = csv.reader(f)
    next(r) # skip the header row
    for row in r:
        if row[1] not in usa_spending:
            usa_spending[row[1]] = {}
            for y in spending_years:
                usa_spending[row[1]][y] = Decimal(0)
        if row[0] in spending_years:
            usa_spending[row[1]][row[0]] += Decimal(row[3])

# build a markdown file for each program using Jekyll's required format
for l in assistance_listings_list:
    with open('../website/_program/'+l['data']['programNumber']+'.md', 'w') as file:
        file.write('---\n') # Begin Jekyll Front Matter
        listing = {
            'cfda': l['data']['programNumber'],
            'title': l['data']['title'],
            'objective': l['data']['objective'],
            'assistance_types': [],
            'beneficiary_types': [],
            'applicant_types': [],
            'categories': sorted(category_list.get(l['data']['programNumber'],'')),
            'agency': '',
            'sub-agency': '',
            'obligations': ''
        }

        data = set()
        for e in l['data']['financial']['obligations']:
            if e.get('assistanceType', False):
                data.add(e['assistanceType'])
        for d in data:
            listing['assistance_types'].append(assistance_types.get(d,''))
        listing['assistance_types'] = sorted(listing['assistance_types'])
        
        for e in l['data']['eligibility']['beneficiary']['types']:
            listing['beneficiary_types'].append(beneficiary_types[e])
        listing['beneficiary_types'] = sorted(listing['beneficiary_types'])
        
        for e in l['data']['eligibility']['applicant']['types']:
            listing['applicant_types'].append(applicant_types[e])
        listing['applicant_types'] = sorted(listing['applicant_types'])

        if organizations_list.get(int(l['data']['organizationId']), False):
            listing['agency'] = organizations_list[int(l['data']['organizationId'])]['agency']
            listing['sub-agency'] = organizations_list[int(l['data']['organizationId'])]['sub-agency']

        s = []
        for y in spending_years:
            sam_estimate = 0.0
            sam_actual = 0.0
            usa_obligations = 0.0
            if l['data']['programNumber'] in sam_spending and y in sam_spending[l['data']['programNumber']]:
                if 'estimate' in sam_spending[l['data']['programNumber']][y]:
                    sam_estimate = float(sam_spending[l['data']['programNumber']][y]['estimate'])
                if 'actual' in sam_spending[l['data']['programNumber']][y]:
                    sam_actual = float(sam_spending[l['data']['programNumber']][y]['actual'])
            if l['data']['programNumber'] in usa_spending and y in usa_spending[l['data']['programNumber']]:
                usa_obligations = float(usa_spending[l['data']['programNumber']][y])
            s.append({'key': 'SAM.gov Estimate', 'year': y, 'amount': sam_estimate})
            s.append({'key': 'SAM.gov Actual', 'year': y, 'amount': sam_actual})
            s.append({'key': 'USASpending.gov Obligations', 'year': y, 'amount': usa_obligations})
        listing['obligations'] = json.dumps(s)
        
        yaml.dump(listing, file)
        file.write('---\n') # End Jekyll Front Matter