import csv
import json
import yaml
from decimal import Decimal

FISCAL_YEAR = '2022'

# converts a string (e.g., category name) to a URL-safe string
def convert_to_url_string(s):
    return ''.join(c if c.isalnum() else '-' for c in s.lower())

# given a subset of programs, generates a list of dictionaries that contain
# agency title, number of programs, and total obligations
def generate_agency_list(list_of_programs, all_programs):
    _agencies = {}
    for p in list_of_programs:
        # skip the program if it has been archived
        if not p in programs:
            continue
        if all_programs[p].get('agency', 'Not Available') not in _agencies:
            _agencies[all_programs[p].get('agency', 'Not Available')] = {
                'title': all_programs[p].get('agency', 'Not Available'),
                'total_num_programs': 0,
                'total_obs': Decimal(0)
            }
        _agencies[all_programs[p].get('agency', 'Not Available')]['total_num_programs'] += 1
        _agencies[all_programs[p].get('agency', 'Not Available')]['total_obs'] += all_programs[p]['total_obs']
    
    r = []
    for a in _agencies:
        _agencies[a]['total_obs'] = int(_agencies[a]['total_obs'])
        r.append(_agencies[a])
    return r


# given a subset of programs, generates a list of dictionaries that contain
# agency title, number of programs, and total obligations
def generate_applicant_type_list(list_of_programs, all_programs):
    _applicant_types = {}
    for p in list_of_programs:
        # skip the program if it has been archived
        if not p in all_programs:
            continue
        for at in all_programs[p]['applicant_types']:
            if at not in _applicant_types:
                _applicant_types[at] = {
                    'title': at,
                    'total_num_programs': 0
                }
            _applicant_types[at]['total_num_programs'] += 1
    
    r = []
    for a in _applicant_types:
       r.append(_applicant_types[a])
    return r

with open('source_files/assistance-listings.json') as f:
    assistance_listings_list = json.load(f)

with open('source_files/dictionary.json') as f:
    dictionary_list = json.load(f)
    
with open('source_files/organizations.json') as f:
    organizations_list = json.load(f)

# load applicant types into dictionary
for i in dictionary_list['_embedded']['jSONObjectList']:
    if i['id'] == 'applicant_types':
        applicant_types = {}
        for e in i['elements']:
            applicant_types[e['element_id']] = e['value']

# load organization data into dictionary
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

# load assistance listings
programs = {}
for l in assistance_listings_list:
    listing = {
        'cfda': l['data']['programNumber'],
        'title': l['data']['title'],
        'applicant_types': [],
        'agency': '',
        'total_obs': Decimal(0)
    }

    # load agency name, if exists
    if organizations_list.get(int(l['data']['organizationId']), False):
        listing['agency'] = organizations_list[int(l['data']['organizationId'])]['agency']

    # load SAM.gov financial obligations for FISCAL_YEAR (actual)
    for o in l['data']['financial']['obligations']:
        for row in o.get('values', []):
            if str(row['year']) == FISCAL_YEAR:
                val = row.get('actual', Decimal(0))
                if val:
                    listing['total_obs'] += Decimal(val)

    for e in l['data']['eligibility']['applicant']['types']:
        listing['applicant_types'].append(applicant_types[e])

    listing['applicant_types'] = sorted(listing['applicant_types'])
    programs[str(l['data']['programNumber'])] = listing

# load category data
category_list = {}
subcategory_list = {}
with open('source_files/2022-program-to-function-sub-function.csv', newline='') as f:
    r = csv.reader(f)
    for row in r:

        # load categories into dictionary
        if row[1] not in category_list:
            category_list[row[1]] = {
                'title': row[1],
                'permalink': '/category/'+convert_to_url_string(row[1]),
                'fiscal_year': FISCAL_YEAR,
                'total_num_programs': 0,
                'total_num_sub_cats': 0,
                'total_num_agencies': 0,
                'total_num_applicant_types': 0,
                'total_obs': Decimal(0),
                'sub_cats': [],
                'agencies': [],
                'applicant_types': [],
                '_programs': set(),
                '_sub_cats': {}
            }
        
        # load sub-categories into dictionary
        if (row[1], row[2]) not in subcategory_list:
            subcategory_list[(row[1], row[2])] = {
                'title': row[2],
                'permalink': '/category/'+convert_to_url_string(row[1])+'/'+convert_to_url_string(row[2]),
                'parent_title': row[1],
                'parent_permalink': '/category/'+convert_to_url_string(row[1]),
                'fiscal_year': FISCAL_YEAR,
                'total_obs': Decimal(0),
                'total_num_programs': 0,
                'total_num_agencies': 0,
                'total_num_applicant_types': 0,
                'agencies': [], # agencies
                'applicant_types': [], # applicant types
                'programs': [], # programs
                '_programs': set()
            }
        
        # add sub-cats (and respective program IDs) to cat
        if row[2] not in category_list[row[1]]['_sub_cats']:
            category_list[row[1]]['_sub_cats'][row[2]] = set()
        category_list[row[1]]['_sub_cats'][row[2]].add(row[0])

        # add the program ID to the cat and sub-cat set
        category_list[row[1]]['_programs'].add(row[0])
        subcategory_list[(row[1], row[2])]['_programs'].add(row[0])

""" Generate Categories """
for c in category_list:

    # calculate total obligations and number of programs for the cat
    for p in category_list[c]['_programs']:
        # skip the program if it has been archived
        if not p in programs:
            continue
        category_list[c]['total_num_programs'] += 1
        category_list[c]['total_obs'] += programs[p]['total_obs']

    # calculate the sub-cats, including number of programs and obligations
    for sc in category_list[c]['_sub_cats']:
        category_list[c]['total_num_sub_cats'] += 1
        sub_cat = {
            'title': subcategory_list[(c, sc)]['title'],
            'permalink': subcategory_list[(c, sc)]['permalink'],
            'total_num_programs': 0,
            'total_obs': Decimal(0)
        }
        for p in category_list[c]['_sub_cats'][sc]:
            # skip the program if it has been archived
            if not p in programs:
                continue
            sub_cat['total_num_programs'] += 1
            sub_cat['total_obs'] += programs[p]['total_obs']
        sub_cat['total_obs'] = int(sub_cat['total_obs'])
        category_list[c]['sub_cats'].append(sub_cat)
    
    # set total number of applicant types and agencies
    category_list[c]['total_num_agencies'] = len(generate_agency_list(category_list[c]['_programs'], programs))
    category_list[c]['total_num_applicant_types'] = len(generate_applicant_type_list(category_list[c]['_programs'], programs))

    # convert to the necessary format for frontend rendering
    category_list[c]['total_obs'] = int(category_list[c]['total_obs'])
    category_list[c]['sub_cats'] = json.dumps(category_list[c]['sub_cats'])
    category_list[c]['agencies'] = json.dumps(generate_agency_list(category_list[c]['_programs'], programs))
    category_list[c]['applicant_types'] = json.dumps(generate_applicant_type_list(category_list[c]['_programs'], programs))
    category_list[c].pop('_programs', None)
    category_list[c].pop('_sub_cats', None)
    
    # build a markdown file for each program using Jekyll's required format
    with open('../website/_category/'+convert_to_url_string(category_list[c]['title'])+'.md', 'w') as file:
        file.write('---\n') # Begin Jekyll Front Matter
        yaml.dump(category_list[c], file)
        file.write('---\n') # End Jekyll Front Matter


""" Generate Sub-categories """
for sc in subcategory_list:
    
    # calculate total obligations and number of programs for the sub-cat, agency, and applicant types
    for p in subcategory_list[sc]['_programs']:
        # skip the program if it has been archived
        if not p in programs:
            continue
        subcategory_list[sc]['total_num_programs'] += 1
        subcategory_list[sc]['total_obs'] += programs[p]['total_obs']
        
        _p = programs[p].copy()
        _p['permalink'] = '/program/'+_p['cfda']
        _p['total_obs'] = int(_p['total_obs'])
        _p.pop('applicant_types', None)
        subcategory_list[sc]['programs'].append(_p)
    
    # set total number of applicant types and agencies
    subcategory_list[sc]['total_num_agencies'] = len(generate_agency_list(subcategory_list[sc]['_programs'], programs))
    subcategory_list[sc]['total_num_applicant_types'] = len(generate_applicant_type_list(subcategory_list[sc]['_programs'], programs))

    # convert to the necessary format for frontend rendering
    subcategory_list[sc]['agencies'] = json.dumps(generate_agency_list(subcategory_list[sc]['_programs'], programs))
    subcategory_list[sc]['applicant_types'] = json.dumps(generate_applicant_type_list(subcategory_list[sc]['_programs'], programs))
    subcategory_list[sc]['programs'] = json.dumps(subcategory_list[sc]['programs'])
    subcategory_list[sc]['total_obs'] = int(subcategory_list[sc]['total_obs'])
    subcategory_list[sc].pop('_programs', None)

    # build a markdown file for each program using Jekyll's required format
    with open('../website/_subcategory/'+convert_to_url_string(subcategory_list[sc]['parent_title'])+'---'+convert_to_url_string(subcategory_list[sc]['title'])+'.md', 'w') as file:
        file.write('---\n') # Begin Jekyll Front Matter
        yaml.dump(subcategory_list[sc], file)
        file.write('---\n') # End Jekyll Front Matter
