import csv
import json
import yaml
from decimal import Decimal
from typing import Optional

FISCAL_YEARS = ['2019', '2020', '2021', '2022', '2023']

"""                    """
""" BEGIN OBJECT SETUP """
"""                    """

class GenericCategory:
    def __init__(self, id: str, title: str, type: str) -> None:
        self.id: str = id
        self.title: str = title
        self.type: str = type
        self.parent: GenericCategory = None
        self.programs: set[Program] = set()

    def add_program(self, p: 'GenericCategory') -> None:
        self.programs.add(p)

    def set_parent(self, parent: 'GenericCategory') -> None:
        self.parent = parent

class Agency(GenericCategory):
    def __init__(self, id: str, title: str) -> None:
        self.id: str = id
        self.title: str = title
        self.type: str = 'agency'
        self.parent: 'Agency' = None
        self.programs: set[Program] = set()

    def set_parent(self, parent: 'Agency') -> None:
        self.parent = parent

    def get_top_level_agency(self) -> 'GenericCategory':
        agency = self
        while agency.parent is not None:
            agency = agency.parent
        return agency

    def get_second_level_agency(self) -> Optional['GenericCategory']:
        agency = self
        while agency.parent is not None:
            if agency.parent.parent is None:
                return agency
            agency = agency.parent
        return None

class Program:
    def __init__(self, id: str, title: str, fiscal_years: list[str]) -> None:
        self.id: str = id
        self.title: str = title
        self.agency: Optional[Agency] = None
        self.applicant_types: set[GenericCategory] = set()
        self.assistance_types: set[GenericCategory] = set()
        self.beneficiary_types: set[GenericCategory] = set()
        self.categories: set[GenericCategory] = set()
        self.spending: dict[str, GenericCategory] = {}
        self.objective: str = ''
        self.fiscal_years: list[str] = fiscal_years
        self.contruct_spending_objects()

    def contruct_spending_objects(self) -> None:
        for y in self.fiscal_years:
            self.spending[y] = ProgramSpendingYear(y)

    def set_agency(self, agency: Optional[GenericCategory]) -> None:
        if agency is not None:
            self.agency = agency

    def set_objective(self, objective: str) -> None:
        self.objective = objective

    def add_category(self, type: str, category: GenericCategory) -> None:
        getattr(self, type).add(category)
    
    def add_spending(self, year: str, type: str, amount: Decimal) -> None:
        if year not in self.fiscal_years:
            return
        current_amount = getattr(self.spending[year], type)
        if current_amount is None:
            current_amount = Decimal(0)
        setattr(self.spending[year], type, current_amount + amount)
    
    def get_id(self) -> str:
        return self.id

    def get_title(self) -> str:
        return self.title
    
    def get_objective(self) -> str:
        return self.objective
    
    def get_category_printable_list(self, type: str, exclude_top_level: bool = False) -> list[str]:
        r = []
        for c in getattr(self, type):
            if c.parent is not None:
                for p in getattr(self, type):
                    if p.id == c.parent.id:
                        r.append(p.title + ' - ' + c.title)
            elif not exclude_top_level:
                r.append(c.title)
        return sorted(r)
    
    def get_top_level_agency_printable(self) -> str:
        if self.agency is None:
            return 'N/A'
        return self.agency.get_top_level_agency().title

    def get_second_level_agency_printable(self) -> str:
        if self.agency is None or self.agency.get_second_level_agency() is None:
            return 'N/A'
        return self.agency.get_second_level_agency().title
        
    def get_obligations_json(self, return_zeros: bool = True) -> str:
        r = []
        for y in self.spending:
            r += self.spending[y].get_list_of_dicts_per_year_per_value(return_zeros)
        return json.dumps(r)

class ProgramSpendingYear:
    def __init__(self, year: str) -> None:
        self.year: str = year
        self.sam_estimate: Decimal = None
        self.sam_actual: Decimal = None
        self.usa_spending_actual: Decimal = None
    
    def get_list_of_dicts_per_year_per_value(self, return_zeros: bool = True) -> list[dict]:
        sam_estimate = float(self.sam_estimate) if self.sam_estimate else None
        sam_actual = float(self.sam_actual) if self.sam_actual else None
        usa_spending_actual = float(self.usa_spending_actual) if self.usa_spending_actual else None
        if return_zeros:
            sam_estimate = sam_estimate if sam_estimate else float(0.0)
            sam_actual = sam_actual if sam_actual else float(0.0)
            usa_spending_actual = usa_spending_actual if usa_spending_actual else float(0.0)
        return [
            {'key': 'SAM.gov Estimate', 'year': self.year, 'amount': sam_estimate},
            {'key': 'SAM.gov Actual', 'year': self.year, 'amount': sam_actual},
            {'key': 'USASpending.gov Obligations', 'year': self.year, 'amount': usa_spending_actual}
        ]

def convert_to_url_string(s: str) -> str:
    return str(''.join(c if c.isalnum() else '-' for c in s.lower()))

assistance_types: dict[str, GenericCategory] = {}
applicant_types: dict[str, GenericCategory] = {}
beneficiary_types: dict[str, GenericCategory] = {}
with open('source_files/dictionary.json') as f:
    dictionary_list = json.load(f)
    for i in dictionary_list['_embedded']['jSONObjectList']:
        if i['id'] == 'assistance_type':
            for e in i['elements']:
                for s in e['elements']:
                    assistance_types[str(s['element_id'])] = GenericCategory(str(s['element_id']), str(s['value']), 'assistance_type')
        if i['id'] == 'applicant_types':
            for e in i['elements']:
                applicant_types[str(e['element_id'])] = GenericCategory(str(e['element_id']), str(e['value']), 'applicant_type')
        if i['id'] == 'beneficiary_types':
            for e in i['elements']:
                beneficiary_types[str(e['element_id'])] = GenericCategory(str(e['element_id']), str(e['value']), 'beneficiary_type')

agencies: dict = {}
with open('source_files/organizations.json') as f:
    organizations_list = json.load(f)
    # create and load Agency objects
    for o in organizations_list:
        agencies[str(o['orgKey'])] = Agency(str(o['orgKey']), str(o.get('agencyName', o.get('name', ''))))
    # assign parent Agency object, where appropriate
    for o in organizations_list:
        if o.get('parentOrgKey', False) and agencies.get(str(o['parentOrgKey']), False):
            agencies[str(o['orgKey'])].set_parent(agencies[str(o['parentOrgKey'])])

categories: dict = {}
with open('source_files/2022-program-to-function-sub-function.csv', newline='') as f:
    r = csv.reader(f)
    for row in r:
        if convert_to_url_string(row[1]) not in categories:
            categories[convert_to_url_string(row[1])] = GenericCategory(convert_to_url_string(row[1]), str(row[1]), 'category')
        if convert_to_url_string(row[1]+'---'+row[2]) not in categories:
            categories[convert_to_url_string(row[1]+'---'+row[2])] = GenericCategory(convert_to_url_string(row[1]+'---'+row[2]), str(row[2]), 'category')
            categories[convert_to_url_string(row[1]+'---'+row[2])].set_parent(categories[convert_to_url_string(row[1])])

programs: dict = {}
with open('source_files/assistance-listings.json') as f:
    assistance_listings_list = json.load(f)
    for l in assistance_listings_list:
        d = l['data']
        program = Program(str(d['programNumber']), str(d['title']), FISCAL_YEARS)
        program.set_agency(agencies.get(str(d['organizationId']), None))
        program.set_objective(str(d['objective']))
        programs[str(l['data']['programNumber'])] = program
        for o in l['data']['financial']['obligations']:
            for row in o.get('values', []):
                if str(row['year']) in FISCAL_YEARS:
                    if row.get('actual'):
                        program.add_spending(str(row['year']), 'sam_actual', Decimal(row['actual']))
                    if row.get('estimate'):
                        program.add_spending(str(row['year']), 'sam_estimate', Decimal(row['estimate']))
        for e in l['data']['financial']['obligations']:
            if e.get('assistanceType', False):
                program.add_category('assistance_types', assistance_types[e['assistanceType']])
                assistance_types[e['assistanceType']].add_program(program)
        for e in l['data']['eligibility']['beneficiary']['types']:
                program.add_category('beneficiary_types', beneficiary_types[e])
                beneficiary_types[e].add_program(program)
        for e in l['data']['eligibility']['applicant']['types']:
                program.add_category('applicant_types', applicant_types[e])
                applicant_types[e].add_program(program)

# populate USASpending.gov data into Programs
with open('source_files/usaspending_db_obligations_by_program.csv', newline='') as f:
    r = csv.reader(f)
    next(r) # skip the header row
    for row in r:
        if str(row[1]) in programs:
            programs[str(row[1])].add_spending(str(row[0]), 'usa_spending_actual', Decimal(row[3]))

# populate Programs into Categories
with open('source_files/2022-program-to-function-sub-function.csv', newline='') as f:
    r = csv.reader(f)
    for row in r:
        if str(row[0]) in programs:
            program = programs[str(row[0])]
            category = categories[convert_to_url_string(row[1])]
            subcategory = categories[convert_to_url_string(row[1]+'---'+row[2])]
            program.add_category('categories', category)
            program.add_category('categories', subcategory)
            category.add_program(program)
            subcategory.add_program(program)

"""                  """
""" END OBJECT SETUP """
"""                  """

# build a markdown file for each program using Jekyll's required format
for p in programs:
    program = programs[p]
    with open('../website/_program/'+program.get_id()+'.md', 'w') as file:
        file.write('---\n') # Begin Jekyll Front Matter
        listing = {
            'cfda': program.get_id(),
            'title': program.get_title(),
            'objective': program.get_objective(),
            'assistance_types': program.get_category_printable_list('assistance_types'),
            'beneficiary_types': program.get_category_printable_list('beneficiary_types'),
            'applicant_types': program.get_category_printable_list('applicant_types'),
            'categories': program.get_category_printable_list('categories', True),
            'agency': program.get_top_level_agency_printable(),
            'sub-agency': program.get_second_level_agency_printable(),
            'obligations': program.get_obligations_json()
        }
        yaml.dump(listing, file)
        file.write('---\n') # End Jekyll Front Matter