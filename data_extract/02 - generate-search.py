import csv
import json
import yaml
from decimal import Decimal
from operator import itemgetter
from typing import Optional

FISCAL_YEARS: list[str] = ['2022', '2023', '2024'] # this is the list of fiscal years calculated
PRIMARY_FISCAL_YEAR: str = '2022' # this is the primary year used / displayed across the site
DISPLAY_ENUM_ASSISTANCE_TYPES: dict[str, str] = {
    'FORMULA GRANTS': 'Formula Grants',
    'PROJECT GRANTS': 'Project Grants',
    'DIRECT PAYMENTS FOR A SPECIFIED USE': 'Direct Payments for a Specified Use',
    'DIRECT PAYMENTS WITH UNRESTRICTED USE': 'Direct Payments with Unrestricted Use',
    'DIRECT LOANS': 'Direct Loans',
    'GUARANTEED/INSURED LOANS': 'Guaranteed / Insured Loans',
    'INSURANCE': 'Insurance',
    'SALE, EXCHANGE, OR DONATION OF PROPERTY OR GOODS': 'Sale, Exchange, or Donation of Property or Goods',
    'USE OF PROPERTY, FACILITIES, OR EQUIPMENT': 'Use of Property, Facilities, or Equipment',
    'PROVISION OF SPECIALIZED SERVICES': 'Provision of Specialized Services',
    'ADVISORY SERVICES AND COUNSELING': 'Advisory Services and Counseling',
    'DISSEMINATION OF TECHNICAL INFORMATION': 'Dissemination of Technical Information',
    'TRAINING': 'Training',
    'INVESTIGATION OF COMPLAINTS': 'Investigation of Complaints',
    'FEDERAL EMPLOYMENT': 'Federal Employment',
    'SALARIES AND EXPENSES': 'Salaries and Expenses',
}
DISPLAY_ENUM_AGENCIES: dict[str, str] = {
    'Unspecified': 'Unspecified',
    'IMMEDIATE OFFICE OF THE SECRETARY OF DEFENSE': 'Immediate Office of the Secretary of Defense',
    'FOREIGN AGRICULTURAL SERVICE': 'Foreign Agricultural Service',
    'FEDERAL RAILROAD ADMINISTRATION': 'Federal Railroad Administration',
    'NUCLEAR REGULATORY COMMISSION': 'Nuclear Regulatory Commission',
    'Office of Career, Technical, and Adult Education': 'Office Of Career, Technical, And Adult Education',
    'DEPT OF THE NAVY': 'Department Of The Navy',
    'INSULAR AFFAIRS': 'Insular Affairs',
    'THE INSTITUTE OF MUSEUM AND LIBRARY SERVICES': 'The Institute of Museum and Library Services',
    'AGENCY FOR INTERNATIONAL DEVELOPMENT': 'Agency for International Development',
    'OFFICE OF SPECIAL EDUCATION AND REHABILITATIVE SERVICES': 'Office of Special Education and Rehabilitative Services',
    'INDIAN HEALTH SERVICE': 'Indian Health Service',
    'ANIMAL AND PLANT HEALTH INSPECTION SERVICE': 'Animal and Plant Health Inspection Service',
    'MINE SAFETY AND HEALTH ADMINISTRATION': 'Mine Safety and Health Administration',
    'GENERAL SERVICES ADMINISTRATION': 'General Services Administration',
    'NATIONAL CEMETERY SYSTEM': 'National Cemetery System',
    'FEDERAL BUREAU OF INVESTIGATION': 'Federal Bureau of Investigation',
    'FARM SERVICE AGENCY': 'Farm Service Agency',
    'LABOR, DEPARTMENT OF': 'Department of Labor',
    'NATIONAL ARCHIVES AND RECORDS ADMINISTRATION': 'National Archives and Records Administration',
    'DEFENSE THREAT REDUCTION AGENCY (DTRA)': 'Defense Threat Reduction Agency (DTRA)',
    'OFFICE OF OVERSEAS SCHOOLS': 'Office of Overseas Schools',
    'RURAL HOUSING SERVICE': 'Rural Housing Service',
    'OFFICE OF THE DIRECTOR OF NATIONAL INTELLIGENCE': 'Office of the Director Of National Intelligence',
    'STATE, DEPARTMENT OF': 'Department of State',
    'ADMINISTRATION FOR CHILDREN AND FAMILIES': 'Administration for Children and Families',
    'RURAL UTILITIES SERVICE': 'Rural Utilities Service',
    'DEPT OF THE AIR FORCE': 'Department of the Air Force',
    'NATIONAL AERONAUTICS AND SPACE ADMINISTRATION': 'National Aeronautics and Space Administration',
    'JAPAN-U.S. FRIENDSHIP COMMISSION': 'Japan-U.S. Friendship Commission',
    'USDA, OFFICE OF THE CHIEF ECONOMIST': 'Office of the Chief Economist',
    'DEFENSE HEALTH AGENCY (DHA)': 'Defense Health Agency (DHA)',
    'OFFICE OF THE ASSISTANT SECRETARY FOR ADMINISTRATION (ASA)': 'Office Of The Assistant Secretary For Administration (ASA)',
    'RURAL BUSINESS COOPERATIVE SERVICE': 'Rural Business Cooperative Service',
    'FOREST SERVICE': 'Forest Service',
    'U.S. IMMIGRATION AND CUSTOMS ENFORCEMENT': 'U.S. Immigration and Customs Enforcement',
    'NATIONAL CREDIT UNION ADMINISTRATION': 'National Credit Union Administration',
    'EMPLOYEE BENEFITS SECURITY ADMINISTRATION': 'Employee Benefits Security Administration',
    'UNDER SECRETARY FOR BENEFITS/VETERANS BENEFITS ADMINISTATION': 'Under Secretary for Benefits / Veterans Benefits Administation',
    'OFFICE OF ELEMENTARY AND SECONDARY EDUCATION': 'Office of Elementary and Secondary Education',
    'NATIONAL ENDOWMENT FOR THE ARTS': 'National Endowment for the Arts',
    'DRUG ENFORCEMENT ADMINISTRATION': 'Drug Enforcement Administration',
    'EQUAL EMPLOYMENT OPPORTUNITY COMMISSION': 'Equal Employment Opportunity Commission',
    'CONSUMER PRODUCT SAFETY COMMISSION': 'Consumer Product Safety Commission',
    'ECONOMIC DEVELOPMENT ADMINISTRATION': 'Economic Development Administration',
    'MILLENNIUM CHALLENGE CORPORATION': 'Millennium Challenge Corporation',
    'TRANSPORTATION, DEPARTMENT OF': 'Department of Transportation',
    'WOMEN\'S BUREAU': 'Women\'s Bureau',
    'OFFICE OF ASSISTANT SECRETARY FOR HEALTH': 'Office of Assistant Secretary for Health',
    'Office of the Secretary of Defense': 'Office of the Secretary of Defense',
    'SOUTHEAST CRESCENT REGIONAL COMMISSION': 'Southeast Crescent Regional Commission',
    'NATIONAL INSTITUTE OF STANDARDS AND TECHNOLOGY': 'National Institute of Standards and Technology',
    'OFFICE OF THE NATIONAL COORDINATOR FOR HEALTH INFORMATION TECHNOLOGY (ONC)': 'Office of the National Coordinator for Health Information Technology (ONC)',
    'DELTA REGIONAL AUTHORITY': 'Delta Regional Authority',
    'NATIONAL INSTITUTE OF FOOD AND AGRICULTURE': 'National Institute of Food and Agriculture',
    'Office of Community Planning and Development': 'Office of Community Planning and Development',
    'ADMINISTRATION FOR COMMUNITY LIVING (ACL)': 'Administration for Community Living (ACL)',
    'INSTITUTE OF EDUCATION SCIENCES': 'Institute of Education Sciences',
    'US GEOLOGICAL SURVEY': 'U.S. Geological Survey',
    'SUBSTANCE ABUSE AND MENTAL HEALTH SERVICES ADMINISTRATION': 'Substance Abuse and Mental Health Services Administration',
    'SECRETARY\'S OFFICE OF GLOBAL WOMEN\'S ISSUES': 'Secretary\'s Office Of Global Women\'s Issues',
    'U.S. COAST GUARD': 'U.S. Coast Guard',
    'DEPT OF DEFENSE': 'Department of Defense',
    'AGENCY FOR HEALTHCARE RESEARCH AND QUALITY': 'Agency for Healthcare Research and Quality',
    'U.S. Permanent Mission to the Organization of American States': 'U.S. Permanent Mission to the Organization of American States',
    'DEPARTMENTAL MANAGEMENT': 'Departmental Management',
    'U.S. FISH AND WILDLIFE SERVICE': 'U.S. Fish and Wildlife Service',
    'SMALL BUSINESS ADMINISTRATION': 'Small Business Administration',
    'VETERANS AFFAIRS, DEPARTMENT OF': 'Department of Veterans Affairs',
    'BUREAU OF SAFETY AND ENVIRONMENTAL ENFORCEMENT': 'Bureau of Safety and Environmental Enforcement',
    'EDUCATION, DEPARTMENT OF': 'Department of Education',
    'U.S. ARMY CORPS OF ENGINEERS - CIVIL PROGRAM FINANCING ONLY': 'U.S. Army Corps of Engineers - Civil Program Financing Only',
    'VETERANS BENEFITS ADMINISTRATION': 'Veterans Benefits Administration',
    'FEDERAL AVIATION ADMINISTRATION': 'Federal Aviation Administration',
    'OFFICE OF LOCAL DEFENSE COMMUNITY COOPERATION': 'Office of Local Defense Community Cooperation',
    'ASSISTANT SECRETARY FOR COMMUNITY PLANNING AND DEVELOPMENT': 'Assistant Secretary for Community Planning and Development',
    'ENVIRONMENTAL PROTECTION AGENCY': 'Environmental Protection Agency',
    'EXECUTIVE OFFICE OF THE PRESIDENT': 'Executive Office of the President',
    'DEPT OF THE ARMY': 'Department of the Army',
    'U.S. CITIZENSHIP AND IMMIGRATION SERVICES': 'U.S. Citizenship and Immigration Services',
    'LIBRARY OF CONGRESS': 'Library of Congress',
    'DENALI COMMISSION': 'Denali Commission',
    'UNIFORMED SERVICES UNIVERSITY OF THE HEALTH SCIENCES  (USUHS)': 'Uniformed Services University of the Health Sciences  (USUHS)',
    'FOOD AND DRUG ADMINISTRATION': 'Food and Drug Administration',
    'BUREAU OF OCEAN ENERGY MANAGEMENT': 'Bureau of Ocean Energy Management',
    'OFFICE OF HUMAN RESOURCES AND ADMINISTRATION': 'Office of Human Resources and Administration',
    'EXPORT-IMPORT BANK OF THE U.S.': 'Export-Import Bank of the U.S.',
    'BUREAU OF LABOR STATISTICS': 'Bureau of Labor Statistics',
    'ASSISTANT SECRETARY FOR POLICY DEVELOPMENT AND RESEARCH': 'Assistant Secretary for Policy Development and Research',
    'NATIONAL HIGHWAY TRAFFIC SAFETY ADMINISTRATION': 'National Highway Traffic Safety Administration',
    'HEALTH RESOURCES AND SERVICES ADMINISTRATION': 'Health Resources and Services Administration',
    'OFFICE OF THE COORDINATOR FOR CYBER ISSUES': 'Office of the Coordinator for Cyber Issues',
    'EMPLOYMENT AND TRAINING ADMINISTRATION': 'Employment and Training Administration',
    'FEDERAL COMMUNICATIONS COMMISSION': 'Federal Communications Commission',
    'OFFICE OF DISABILITY EMPLOYMENT POLICY': 'Office of Disability Employment Policy',
    'ENERGY, DEPARTMENT OF': 'Department of Energy',
    'ELECTION ASSISTANCE COMMISSION': 'Election Assistance Commission',
    'DENALI COMMISSION': 'Denali Commission',
    'BUREAU OF RECLAMATION': 'Bureau of Reclamation',
    'FOOD AND NUTRITION SERVICE': 'Food and Nutrition Service',
    'NATIONAL PARK SERVICE': 'National Park Service',
    'EDUCATION, DEPARTMENT OF': 'Department of Education',
    'FEDERAL COMMUNICATIONS COMMISSION': 'Federal Communications Commission',
    'CENTERS FOR MEDICARE AND MEDICAID SERVICES': 'Centers for Medicare and Medicaid Services',
    'OFFICE OF LABOR-MANAGEMENT STANDARDS': 'Office of Labor-Management Standards',
    'ENERGY, DEPARTMENT OF': 'Department of Energy',
    'SCIENCE AND TECHNOLOGY': 'Science and Technology',
    'INTERNAL REVENUE SERVICE': 'Internal Revenue Service',
    'NORTHERN BORDER REGIONAL COMMISSION': 'Northern Border Regional Commission',
    'COMMUNITY DEVELOPMENT FINANCIAL INSTITUTIONS': 'Community Development Financial Institutions',
    'AGRICULTURAL RESEARCH SERVICE': 'Agricultural Research Service',
    'FEDERAL MEDIATION AND CONCILIATION SERVICE': 'Federal Mediation and Conciliation Service',
    'OFFICE OF JUSTICE PROGRAMS': 'Office of Justice Programs',
    'RAILROAD RETIREMENT BOARD': 'Railroad Retirement Board',
    'AGRICULTURE, DEPARTMENT OF': 'Department of Agriculture',
    'CORPORATION FOR NATIONAL AND COMMUNITY SERVICE': 'Corporation for National and Community Service',
    'DEFENSE POW/MIA OFFICE': 'Defense POW / MIA Office',
    'DEFENSE SECURITY COOPERATION AGENCY': 'Defense Security Cooperation Agency',
    'FEDERAL MOTOR CARRIER SAFETY ADMINISTRATION': 'Federal Motor Carrier Safety Administration',
    'INTERIOR, DEPARTMENT OF THE': 'Department of the Interior',
    'BUREAU OF INTERNATIONAL LABOR AFFAIRS': 'Bureau of International Labor Affairs',
    'OFFICE OF FEDERAL STUDENT AID': 'Office of Federal Student Aid',
    'UNITED STATES AGENCY FOR GLOBAL MEDIA, BBG': 'United States Agency for Global Media, BBG',
    'MINORITY BUSINESS DEVELOPMENT AGENCY': 'Minority Business Development Agency',
    'NNSA': 'NNSA',
    'US CENSUS BUREAU': 'U.S. Census Bureau',
    'FEDERAL HIGHWAY ADMINISTRATION': 'Federal Highway Administration',
    'U.S. SECRET SERVICE': 'U.S. Secret Service',
    'NATIONAL OCEANIC AND ATMOSPHERIC ADMINISTRATION': 'National Oceanic and Atmospheric Administration',
    'INTERNATIONAL TRADE ADMINISTRATION': 'International Trade Administration',
    'OFFICE OF WORKERS COMPENSATION PROGRAM': 'Office of Workers Compensation Program',
    'OFFICE OF SURFACE MINING, RECLAMATION AND ENFORCEMENT': 'Office of Surface Mining, Reclamation and Enforcement',
    'FEDERAL TRANSIT ADMINISTRATION': 'Federal Transit Administration',
    'Countering Weapons of Mass Destruction': 'Countering Weapons of Mass Destruction',
    'Cybersecurity and Infrastructure Security Agency': 'Cybersecurity and Infrastructure Security Agency',
    'FOOD SAFETY AND INSPECTION SERVICE': 'Food Safety and Inspection Service',
    'BUREAU OF ECONOMIC AND BUSINESS AFFAIRS': 'Bureau of Economic and Business Affairs',
    'NATIONAL SECURITY AGENCY/CENTRAL SECURITY SERVICE': 'National Security Agency / Central Security Service',
    'BUREAU OF INDIAN AFFAIRS': 'Bureau of Indian Affairs',
    'ASST SECRETARY FOR HOUSING--FEDERAL HOUSING COMMISSIONER': 'Assistant Secretary for Housing -- Federal Housing Commissioner',
    'HOUSING AND URBAN DEVELOPMENT, DEPARTMENT OF': 'Department of Housing and Urban Development',
    'USDA, Office of Partnerships and Public Engagement': 'Office of Partnerships and Public Engagement',
    'DIRECTORY/NATIONAL CEMETERY ADMINISTRATION': 'Directory / National Cemetery Administration',
    'DEPARTMENTAL OFFICES': 'Departmental Offices',
    'VA HEALTH ADMINISTRATION CENTER': 'VA Health Administration Center',
    'NATURAL RESOURCES CONSERVATION SERVICE': 'Natural Resources Conservation Service',
    'APPALACHIAN REGIONAL COMMISSION': 'Appalachian Regional Commission',
    'IMMEDIATE OFFICE OF THE SECRETARY OF AGRICULTURE': 'Immediate Office of the Secretary of Agriculture',
    'RISK MANAGEMENT AGENCY': 'Risk Management Agency',
    'INTER-AMERICAN FOUNDATION': 'Inter-American Foundation',
    'ASSISTANT SECRETARY FOR FAIR HOUSING AND EQUAL OPPORTUNITY': 'Assistant Secretary for Fair Housing and Equal Opportunity',
    'GULF COAST ECOSYSTEM RESTORATION COUNCIL': 'Gulf Coast Ecosystem Restoration Council',
    'OCCUPATIONAL SAFETY AND HEALTH ADMINISTRATION': 'Occupational Safety and Health Administration',
    'STATE, DEPARTMENT OF': 'Department of State',
    'HEALTH AND HUMAN SERVICES, DEPARTMENT OF': 'Department of Health and Human Services',
    'MORRIS K. UDALL SCHOLARSHIP AND EXCELLENCE IN NATIONAL ENVIRONMENTAL POLICY FOUNDATION': 'Morris K. Udall Scholarship and Excellence in National Environmental Policy Foundation',
    'POLITICAL MILITARY AFFAIRS/ WEAPONS REMOVAL AND ABATEMENT': 'Political Military Affairs / Weapons Removal and Abatement',
    'ASSISTANT SECRETARY FOR PUBLIC AND INDIAN HOUSING': 'Assistant Secretary for Public and Indian Housing',
    'CENTERS FOR DISEASE CONTROL AND PREVENTION': 'Centers for Disease Control and Prevention',
    'ECONOMIC RESEARCH SERVICE': 'Economic Research Service',
    'PIPELINE AND HAZARDOUS MATERIALS SAFETY ADMINISTRATION': 'Pipeline and Hazardous Materials Safety Administration',
    'BUREAU OF INTERNATIONAL SECURITY AND NONPROLIFERATION': 'Bureau of International Security and Nonproliferation',
    'OFFICE TO MONITOR AND COMBAT TRAFFICKING IN PERSONS': 'Office to Monitor and Combat Trafficking in Persons',
    'HOMELAND SECURITY, DEPARTMENT OF': 'Department of Homeland Security',
    'OFFICE OF U.S. GLOBAL AIDS COORDINATOR': 'Office of U.S. Global Aids Coordinator',
    'NATIONAL ENDOWMENT FOR THE HUMANITIES': 'National Endowment for the Humanities',
    'FEDERAL PRISON SYSTEM / BUREAU OF PRISONS': 'Federal Prison System / Bureau of Prisons',
    'CORPORATION FOR NATIONAL AND COMMUNITY SERVICE': 'Corporation for National and Community Service',
    'NATIONAL INSTITUTES OF HEALTH': 'National Institutes of Health',
    'DEFENSE ADVANCED RESEARCH PROJECTS AGENCY  (DARPA)': 'Defense Advanced Research Projects Agency  (DARPA)',
    'NATIONAL AGRICULTURAL STATISTICS SERVICE': 'National Agricultural Statistics Service',
    'FEDERAL FINANCIAL INSTITUTIONS EXAMINATION COUNCIL APPRAISAL SUBCOMMITTEE': 'Federal Financial Institutions Examination Council Appraisal Subcommittee',
    'BUREAU OF LAND MANAGEMENT': 'Bureau of Land Management',
    'FEDERAL EMERGENCY MANAGEMENT AGENCY': 'Federal Emergency Management Agency',
    'TREASURY, DEPARTMENT OF THE': 'Department of the Treasury',
    'NATIONAL TELECOMMUNICATIONS AND INFORMATION ADMINISTRATION': 'National Telecommunications and Information Administration',
    'BARRY GOLDWATER SCHOLARSHIP AND EXCELLENCE IN EDUCATION FUND': 'Barry Goldwater Scholarship and Excellence in Education Fund',
    'DEFENSE INTELLIGENCE AGENCY': 'Defense Intelligence Agency',
    'OFFICE OF THE COORDINATOR OF U.S. ASSISTANCE TO EUROPE AND EURASIA': 'Office of the Coordinator of U.S. Assistance to Europe and Eurasia',
    'NATIONAL SCIENCE FOUNDATION': 'National Science Foundation',
    'WASHINGTON HEADQUARTERS SERVICES (WHS)': 'Washington Headquarters Services (WHS)',
    'AGRICULTURAL MARKETING SERVICE': 'Agricultural Marketing Service',
    'OFFICES, BOARDS AND DIVISIONS': 'Boards and Divisions Offices',
    'UNITED STATES INSTITUTE OF PEACE': 'United States Institute of Peace',
    'SOCIAL SECURITY ADMINISTRATION': 'Social Security Administration',
    'OFFICE OF THE SECRETARY': 'Office of the Secretary',
    'FEDERAL PERMITTING IMPROVEMENT STEERING COUNCIL': 'Federal Permitting Improvement Steering Council',
    'VETERANS EMPLOYMENT AND TRAINING SERVICES': 'Veterans Employment and Training Services',
    'LIBRARY OF CONGRESS': 'Library of Congress',
    'JUSTICE, DEPARTMENT OF': 'Department of Justice',
    'Inter-American Foundation': 'Inter-American Foundation',
    'DEPT OF DEFENSE EDUCATION ACTIVITY (DODEA)': 'Department of Defense Education Activity (DODEA)',
    'National Council on Disability': 'National Council on Disability',
    'OFFICE OF LEAD HAZARD CONTROL AND HEALTHY HOMES': 'Office of Lead Hazard Control and Healthy Homes',
    'IMMED OFFICE OF THE SECRETARY OF HEALTH AND HUMAN SERVICES': 'Immed Office of the Secretary of Health and Human Services',
    'COMMERCE, DEPARTMENT OF': 'Department of Commerce',
    'MARITIME ADMINISTRATION': 'Maritime Administration'
}
CFO_ACT_AGENCIES_LIST: list[str] = [
    'Agency for International Development',
    'Department of Agriculture',
    'Department of Commerce',
    'Department of Defense',
    'Department of Education',
    'Department of Energy',
    'Department of Health and Human Services',
    'Department of Homeland Security',
    'Department of Housing and Urban Development',
    'Department of the Interior',
    'Department of Justice',
    'Department of Labor',
    'Department of State',
    'Department of Transportation',
    'Department of the Treasury',
    'Department of Veterans Affairs',
    'Environmental Protection Agency',
    'General Services Administration',
    'National Aeronautics and Space Administration',
    'National Science Foundation',
    'Nuclear Regulatory Commission',
    'Office of Personnel Management',
    'Small Business Administration',
    'Social Security Administration'
]

"""                    """
""" BEGIN OBJECT SETUP """
"""                    """

class GenericCategory:
    def __init__(self, id: str, title: str, type: str) -> None:
        self.id: str = id
        self.type: str = type
        self.parent: GenericCategory = None
        self.programs: set[Program] = set()
        self.set_title(title)

    def set_title(self, title: str) -> None:
        if self.type == 'assistance_type' and title in DISPLAY_ENUM_ASSISTANCE_TYPES:
            title = DISPLAY_ENUM_ASSISTANCE_TYPES[title]
        self.title = title

    def add_program(self, p: 'GenericCategory') -> None:
        self.programs.add(p)

    def get_id(self) -> str:
        return self.id  

    def get_title(self) -> str:
        return self.title
    
    def get_parent(self) -> 'GenericCategory':
        return self.parent

class Agency(GenericCategory):
    def __init__(self, id: str, title: str) -> None:
        self.id: str = id
        self.type: str = 'agency'
        self.parent: 'Agency' = None
        self.programs: set[Program] = set()
        self.set_title(title)

    def set_title(self, title: str) -> None:
        if title in DISPLAY_ENUM_AGENCIES:
            title = DISPLAY_ENUM_AGENCIES[title]
        self.title = title

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

    def collapse_into_parent(self) -> None:
        if self.parent is None:
            return
        for p in self.programs:
            p.agency = self.parent
            self.parent.add_program(p)

class Program:
    def __init__(self, id: str, title: str, fiscal_years: list[str]) -> None:
        self.id: str = id
        self.title: str = title
        self.agency: Agency = None
        self.applicant_types: set[GenericCategory] = set()
        self.assistance_types: set[GenericCategory] = set()
        self.beneficiary_types: set[GenericCategory] = set()
        self.categories: set[GenericCategory] = set()
        self.spending: dict[str, GenericCategory] = {}
        self.objective: str = ''
        self.sam_url: str = ''
        self.popular_name: str = ''
        self.statute: str = ''
        self.fiscal_years: list[str] = fiscal_years
        for y in self.fiscal_years:
            self.spending[y] = ProgramSpendingYear(y)

    def get_popular_name(self) -> str:
        return self.popular_name

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
    
    def get_category_printable_list(self, type: str, include_top_level: bool = False, include_second_level: bool = False) -> list[str]:
        r = []
        for c in getattr(self, type):
            if include_top_level:
                if c.get_parent() is None:
                    r.append(c.title)
            if include_second_level:
                if c.get_parent() is not None:
                    for p in getattr(self, type):
                        if p.id == c.parent.id:
                            r.append(p.title + ' - ' + c.title)
        return sorted(r)

    def get_top_level_agency_printable(self) -> str:
        return self.agency.get_top_level_agency().title

    def get_second_level_agency_printable(self) -> str:
        if self.agency.get_second_level_agency() is None:
            return 'N/A'
        return self.agency.get_second_level_agency().title

    def get_obligations_json(self, return_zeros: bool = True) -> str:
        r = []
        for y in self.spending:
            r.append(self.spending[y].get_dict_of_spending_values(return_zeros))
        return json.dumps(r, separators=(',', ':'))

    def get_obligation_value(self, year: str, type: str, return_zeros: bool = True) -> float:
        if year not in self.fiscal_years:
            raise Exception("Provided year not in allowed range")
        return self.spending[year].get_obligation_value(type, return_zeros)

class ProgramSpendingYear:
    def __init__(self, year: str) -> None:
        self.year: str = year
        self.sam_estimate: Decimal = None
        self.sam_actual: Decimal = None
        self.usa_spending_actual: Decimal = None

    def get_dict_of_spending_values(self, return_zeros: bool = True) -> dict:
        sam_estimate = float(self.sam_estimate) if self.sam_estimate is not None else None
        sam_actual = float(self.sam_actual) if self.sam_actual is not None else None
        usa_spending_actual = float(self.usa_spending_actual) if self.usa_spending_actual is not None else None
        if sam_actual is not None: # if the actual value is set, no longer pass the estimate value
            sam_estimate = None
        if return_zeros:
            sam_estimate = sam_estimate if sam_estimate is not None else float(0.0)
            sam_actual = sam_actual if sam_actual is not None else float(0.0)
            usa_spending_actual = usa_spending_actual if usa_spending_actual is not None else float(0.0)
        return {'x': self.year, 'sam_estimate': sam_estimate, 'sam_actual': sam_actual, 'usa_spending_actual': usa_spending_actual}

    def get_obligation_value(self, type: str, return_zeros: bool = True) -> float:
        val = float(getattr(self, type)) if getattr(self, type) is not None else None
        if val is None and return_zeros:
            val = float(0.0)
        return val

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
                assistance_types[str(e['element_id'])] = GenericCategory(str(e['element_id']), str(e['value']), 'assistance_type')
                for s in e['elements']:
                    assistance_types[str(s['element_id'])] = GenericCategory(str(s['element_id']), str(s['value']), 'assistance_type')
                    assistance_types[str(s['element_id'])].parent = assistance_types[str(e['element_id'])]
        if i['id'] == 'applicant_types':
            for e in i['elements']:
                applicant_types[str(e['element_id'])] = GenericCategory(str(e['element_id']), str(e['value']), 'applicant_type')
        if i['id'] == 'beneficiary_types':
            for e in i['elements']:
                beneficiary_types[str(e['element_id'])] = GenericCategory(str(e['element_id']), str(e['value']), 'beneficiary_type')

agencies: dict = {}
with open('source_files/organizations.json') as f:
    # insert a default agency, for programs that are incorrectly tagged
    agencies['unspecified'] = Agency('unspecified', 'Unspecified')
    organizations_list = json.load(f)
    # create and load Agency objects
    for o in organizations_list:
        agencies[str(o['orgKey'])] = Agency(str(o['orgKey']), str(o.get('name', '')))
    # assign parent Agency object, where appropriate
    for o in organizations_list:
        if o.get('parentOrgKey', False) and agencies.get(str(o['parentOrgKey']), False):
            agencies[str(o['orgKey'])].parent = agencies[str(o['parentOrgKey'])]

categories: dict = {}
with open('source_files/2022-program-to-function-sub-function.csv', newline='') as f:
    r = csv.reader(f)
    for row in r:
        if convert_to_url_string(row[1]) not in categories:
            categories[convert_to_url_string(row[1])] = GenericCategory(convert_to_url_string(row[1]), str(row[1]), 'category')
        if convert_to_url_string(row[1]+'---'+row[2]) not in categories:
            categories[convert_to_url_string(row[1]+'---'+row[2])] = GenericCategory(convert_to_url_string(row[1]+'---'+row[2]), str(row[2]), 'category')
            categories[convert_to_url_string(row[1]+'---'+row[2])].parent = categories[convert_to_url_string(row[1])]

programs: dict = {}
with open('source_files/assistance-listings.json') as f:
    assistance_listings_list = json.load(f)
    for l in assistance_listings_list:
        d = l['data']
        program = Program(str(d['programNumber']), str(d['title']), FISCAL_YEARS)
        agency = agencies.get('unspecified') # default to 'unspecified' agency
        if agencies.get(str(d['organizationId']), False):
            agency = agencies.get(str(d['organizationId']))
        program.agency = agency
        program.agency.add_program(program)
        if program.agency.get_parent() is not None:
            program.agency.get_parent().add_program(program)
        if len(d.get('alternativeNames', [])) > 0 and len(d['alternativeNames'][0]) > 0: # if the program has an alternative "popular name"
            program.popular_name = d['alternativeNames'][0]
        program.objective = str(d['objective'])
        program.sam_url = 'https://sam.gov/fal/' + l['id'] + '/view'
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
                program.add_category('assistance_types', assistance_types[e['assistanceType']].get_parent())
                assistance_types[e['assistanceType']].add_program(program)
                assistance_types[e['assistanceType']].get_parent().add_program(program)
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

# condense agencies down to two tiers
while len([a for a in agencies if agencies[a].get_parent() is not None and agencies[a].get_parent().get_parent() is not None]):
    remove = []
    for a in agencies:
        if agencies[a].get_parent() is not None and agencies[a].get_parent().get_parent() is not None:
            agencies[a].collapse_into_parent()
            remove.append(a)
    for r in remove:
        agencies.pop(r)

"""                  """
""" END OBJECT SETUP """
"""                  """

# build a markdown file for each program using Jekyll's required format
for p in programs:
    program = programs[p]
    with open('../website/_program/'+program.get_id()+'.md', 'w') as file:
        file.write('---\n') # Begin Jekyll Front Matter
        listing = {
            'title': program.get_title(),
            'layout': 'program',
            'permalink': '/program/' + program.get_id() + '.html',
            'fiscal_year': PRIMARY_FISCAL_YEAR,
            'cfda': program.get_id(),
            'objective': program.objective,
            'sam_url': program.sam_url,
            'popular_name': program.get_popular_name(),
            'assistance_types': program.get_category_printable_list('assistance_types', True),
            'beneficiary_types': program.get_category_printable_list('beneficiary_types', True),
            'applicant_types': program.get_category_printable_list('applicant_types', True),
            'categories': program.get_category_printable_list('categories', False, True),
            'agency': program.get_top_level_agency_printable(),
            'sub-agency': program.get_second_level_agency_printable(),
            'obligations': program.get_obligations_json()
        }
        yaml.dump(listing, file)
        file.write('---\n') # End Jekyll Front Matter

# build a markdown file to enable generation of an all program PDF
with open('../website/pages/pdf.md', 'w') as file:
    _programs_list: list = []
    for p in programs:
        program = programs[p]
        _programs_list.append({
            'title': program.get_title(),
            'layout': 'program',
            'permalink': '/program/' + program.get_id() + '.html',
            'fiscal_year': PRIMARY_FISCAL_YEAR,
            'cfda': program.get_id(),
            'objective': program.objective,
            'sam_url': program.sam_url,
            'popular_name': program.get_popular_name(),
            'assistance_types': program.get_category_printable_list('assistance_types', True),
            'beneficiary_types': program.get_category_printable_list('beneficiary_types', True),
            'applicant_types': program.get_category_printable_list('applicant_types', True),
            'categories': program.get_category_printable_list('categories', False, True),
            'agency': program.get_top_level_agency_printable(),
            'sub-agency': program.get_second_level_agency_printable(),
            'obligations': program.get_obligations_json()
        })
    file.write('---\n') # Begin Jekyll Front Matter
    yaml.dump({
        'title': 'Programs PDF',
        'layout': 'pdf',
        'permalink': '/pdf.html',
        'programs': sorted(_programs_list, key=itemgetter('agency', 'sub-agency'))
    }, file)
    file.write('---\n') # End Jekyll Front Matter

# build a markdown file for each category & sub-category using Jekyll's required format


# build a markdown file for the category index page using Jekyll's required format
with open('../website/pages/category.md', 'w') as file:
    file.write('---\n') # Begin Jekyll Front Matter
    listing = {
        'title': 'Categories',
        'layout': 'category-index',
        'permalink': '/category.html',
        'fiscal_year': PRIMARY_FISCAL_YEAR,

        'total_num_programs': len(programs),
        'total_obs': sum(programs[p].get_obligation_value(PRIMARY_FISCAL_YEAR, 'sam_actual') for p in programs),
        'categories': sorted([
            {
                'title': categories[c].get_title(),
                'permalink': '/category/'+categories[c].get_id(),
            } for c in categories if (categories[c].get_parent() is None)
        ], key=lambda category: category['title']),
        'categories_json': json.dumps(sorted([
            {
                'title': categories[c].get_title(),
                'total_num_programs': len(categories[c].programs),
                'total_obs': sum(p.get_obligation_value(PRIMARY_FISCAL_YEAR, 'sam_actual') for p in categories[c].programs),
                'permalink': '/category/'+categories[c].get_id()
            } for c in categories if (categories[c].get_parent() is None)
        ], key=lambda category: category['total_obs'], reverse=True), separators=(',', ':'))
    }
    yaml.dump(listing, file)
    file.write('---\n') # End Jekyll Front Matter

# build the markdown file for the search page using Jekyll's required format
def generate_list_of_program_ids_for_category(categories: list[GenericCategory], two_tier: bool = False) -> list[dict [str, list[str]]]:
    r: list[dict] = []
    for key in categories:
        category: GenericCategory = categories[key]
        if not two_tier or (two_tier and category.get_parent() is None):
            o = {
                'title': category.get_title(),
                'programs': [p.get_id() for p in category.programs]
            }
            if len(o['programs']) == 0: # if there are no programs, don't add the category
                continue
            if two_tier:
                all_programs: set = set(p.get_id() for p in category.programs)
                o['sub_categories']: list = []
                for child_key in categories:
                    child: GenericCategory = categories[child_key]
                    # only process if the parent is equal to the parent category AND, if the type is an Agency, the child title
                    # is not equal to the parent title. we should skip children that have the same name as the parent, as these
                    # are not "sub-agencies," but rather data anomolies
                    if child.get_parent() == category \
                        and not (child.type == 'agency' and child.get_title() == child.get_parent().get_title()):
                        o['sub_categories'].append(
                            {
                                'title': child.get_title(),
                                'programs': [p.get_id() for p in child.programs]
                            }
                        )
                        all_programs -= set(p.get_id() for p in child.programs)
                if len(all_programs) and len(o['sub_categories']) > 0: # only include the "unspecified" sub-category if there are other sub-categories
                    o['sub_categories'].append(
                        {
                            'title': 'Unspecified',
                            'programs': list(all_programs)
                        }
                    )
            r.append(o)
    return sorted(r, key=lambda cat: cat['title'])

with open('../website/pages/search.md', 'w') as file:
    file.write('---\n') # Begin Jekyll Front Matter
    page = {
        'title': 'Program search',
        'layout': 'search',
        'permalink': '/search.html',
        'fiscal_year': PRIMARY_FISCAL_YEAR,

        'cfo_agencies': [a for a in generate_list_of_program_ids_for_category(agencies, True) if a['title'] in CFO_ACT_AGENCIES_LIST],
        'other_agencies': [a for a in generate_list_of_program_ids_for_category(agencies, True) if a['title'] not in CFO_ACT_AGENCIES_LIST],
        'applicant_types': generate_list_of_program_ids_for_category(applicant_types),
        'assistance_types': generate_list_of_program_ids_for_category(assistance_types, True),
        'beneficiary_types': generate_list_of_program_ids_for_category(beneficiary_types),
        'categories': generate_list_of_program_ids_for_category(categories, True),
        'programs': json.dumps(sorted([
            {
                'cfda': programs[p].get_id(),
                'title': programs[p].get_title(),
                'permalink': '/program/' + programs[p].get_id(),
                'agency': programs[p].get_top_level_agency_printable(),
                'obligations': programs[p].get_obligation_value(PRIMARY_FISCAL_YEAR, 'sam_actual')
            } for p in programs
        ], key=lambda program: program['obligations'], reverse=True), separators=(',', ':'))
    }
    yaml.dump(page, file)
    file.write('---\n') # End Jekyll Front Matter