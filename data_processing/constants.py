"""
Store various constants used across the data processing process.
"""

FISCAL_YEAR = "2024"

AGENCY_DISPLAY_NAMES = {
    "IMMEDIATE OFFICE OF THE SECRETARY OF DEFENSE":
        "Immediate Office of the Secretary of Defense",
    "FOREIGN AGRICULTURAL SERVICE": "Foreign Agricultural Service",
    "FEDERAL RAILROAD ADMINISTRATION": "Federal Railroad Administration",
    "NUCLEAR REGULATORY COMMISSION": "Nuclear Regulatory Commission",
    "Office of Career, Technical, and Adult Education":
        "Office Of Career, Technical, And Adult Education",
    "DEPT OF THE NAVY": "Department Of The Navy",
    "INSULAR AFFAIRS": "Insular Affairs",
    "THE INSTITUTE OF MUSEUM AND LIBRARY SERVICES":
        "The Institute of Museum and Library Services",
    "AGENCY FOR INTERNATIONAL DEVELOPMENT":
        "Agency for International Development",
    "OFFICE OF SPECIAL EDUCATION AND REHABILITATIVE SERVICES":
        "Office of Special Education and Rehabilitative Services",
    "INDIAN HEALTH SERVICE": "Indian Health Service",
    "ANIMAL AND PLANT HEALTH INSPECTION SERVICE":
        "Animal and Plant Health Inspection Service",
    "MINE SAFETY AND HEALTH ADMINISTRATION":
        "Mine Safety and Health Administration",
    "GENERAL SERVICES ADMINISTRATION": "General Services Administration",
    "NATIONAL CEMETERY SYSTEM": "National Cemetery System",
    "FEDERAL BUREAU OF INVESTIGATION": "Federal Bureau of Investigation",
    "FARM SERVICE AGENCY": "Farm Service Agency",
    "LABOR, DEPARTMENT OF": "Department of Labor",
    "NATIONAL ARCHIVES AND RECORDS ADMINISTRATION":
        "National Archives and Records Administration",
    "DEFENSE THREAT REDUCTION AGENCY (DTRA)":
        "Defense Threat Reduction Agency (DTRA)",
    "OFFICE OF OVERSEAS SCHOOLS": "Office of Overseas Schools",
    "RURAL HOUSING SERVICE": "Rural Housing Service",
    "OFFICE OF THE DIRECTOR OF NATIONAL INTELLIGENCE":
        "Office of the Director Of National Intelligence",
    "STATE, DEPARTMENT OF": "Department of State",
    "ADMINISTRATION FOR CHILDREN AND FAMILIES":
        "Administration for Children and Families",
    "RURAL UTILITIES SERVICE": "Rural Utilities Service",
    "DEPT OF THE AIR FORCE": "Department of the Air Force",
    "NATIONAL AERONAUTICS AND SPACE ADMINISTRATION":
        "National Aeronautics and Space Administration",
    "JAPAN-U.S. FRIENDSHIP COMMISSION": "Japan-U.S. Friendship Commission",
    "USDA, OFFICE OF THE CHIEF ECONOMIST": "Office of the Chief Economist",
    "DEFENSE HEALTH AGENCY (DHA)": "Defense Health Agency (DHA)",
    "OFFICE OF THE ASSISTANT SECRETARY FOR ADMINISTRATION (ASA)":
        "Office Of The Assistant Secretary For Administration (ASA)",
    "RURAL BUSINESS COOPERATIVE SERVICE": "Rural Business Cooperative Service",
    "FOREST SERVICE": "Forest Service",
    "U.S. IMMIGRATION AND CUSTOMS ENFORCEMENT":
        "U.S. Immigration and Customs Enforcement",
    "NATIONAL CREDIT UNION ADMINISTRATION":
        "National Credit Union Administration",
    "EMPLOYEE BENEFITS SECURITY ADMINISTRATION":
        "Employee Benefits Security Administration",
    "UNDER SECRETARY FOR BENEFITS/VETERANS BENEFITS ADMINISTATION":
        "Under Secretary for Benefits / Veterans Benefits Administation",
    "OFFICE OF ELEMENTARY AND SECONDARY EDUCATION":
        "Office of Elementary and Secondary Education",
    "NATIONAL ENDOWMENT FOR THE ARTS": "National Endowment for the Arts",
    "DRUG ENFORCEMENT ADMINISTRATION": "Drug Enforcement Administration",
    "EQUAL EMPLOYMENT OPPORTUNITY COMMISSION":
        "Equal Employment Opportunity Commission",
    "CONSUMER PRODUCT SAFETY COMMISSION": "Consumer Product Safety Commission",
    "ECONOMIC DEVELOPMENT ADMINISTRATION":
        "Economic Development Administration",
    "MILLENNIUM CHALLENGE CORPORATION": "Millennium Challenge Corporation",
    "TRANSPORTATION, DEPARTMENT OF": "Department of Transportation",
    "WOMEN'S BUREAU": "Women\'s Bureau",
    "OFFICE OF ASSISTANT SECRETARY FOR HEALTH":
        "Office of Assistant Secretary for Health",
    "Office of the Secretary of Defense": "Office of the Secretary of Defense",
    "SOUTHEAST CRESCENT REGIONAL COMMISSION":
        "Southeast Crescent Regional Commission",
    "NATIONAL INSTITUTE OF STANDARDS AND TECHNOLOGY":
        "National Institute of Standards and Technology",
    "OFFICE OF THE NATIONAL COORDINATOR FOR "
        "HEALTH INFORMATION TECHNOLOGY (ONC)":
            "Office of the National Coordinator for "
            "Health Information Technology (ONC)",
    "DELTA REGIONAL AUTHORITY": "Delta Regional Authority",
    "NATIONAL INSTITUTE OF FOOD AND AGRICULTURE":
        "National Institute of Food and Agriculture",
    "Office of Community Planning and Development":
        "Office of Community Planning and Development",
    "ADMINISTRATION FOR COMMUNITY LIVING (ACL)":
        "Administration for Community Living (ACL)",
    "INSTITUTE OF EDUCATION SCIENCES": "Institute of Education Sciences",
    "US GEOLOGICAL SURVEY": "U.S. Geological Survey",
    "SUBSTANCE ABUSE AND MENTAL HEALTH SERVICES ADMINISTRATION":
        "Substance Abuse and Mental Health Services Administration",
    "SECRETARY\'S OFFICE OF GLOBAL WOMEN\'S ISSUES":
        "Secretary\'s Office Of Global Women\'s Issues",
    "U.S. COAST GUARD": "U.S. Coast Guard",
    "DEPT OF DEFENSE": "Department of Defense",
    "DEPARTMENT OF DEFENSE": "Department of Defense",
    "AGENCY FOR HEALTHCARE RESEARCH AND QUALITY":
        "Agency for Healthcare Research and Quality",
    "U.S. Permanent Mission to the Organization of American States":
        "U.S. Permanent Mission to the Organization of American States",
    "DEPARTMENTAL MANAGEMENT": "Departmental Management",
    "U.S. FISH AND WILDLIFE SERVICE": "U.S. Fish and Wildlife Service",
    "SMALL BUSINESS ADMINISTRATION": "Small Business Administration",
    "VETERANS AFFAIRS, DEPARTMENT OF": "Department of Veterans Affairs",
    "BUREAU OF SAFETY AND ENVIRONMENTAL ENFORCEMENT":
        "Bureau of Safety and Environmental Enforcement",
    "EDUCATION, DEPARTMENT OF": "Department of Education",
    "U.S. ARMY CORPS OF ENGINEERS - CIVIL PROGRAM FINANCING ONLY":
        "U.S. Army Corps of Engineers - Civil Program Financing Only",
    "VETERANS BENEFITS ADMINISTRATION": "Veterans Benefits Administration",
    "FEDERAL AVIATION ADMINISTRATION": "Federal Aviation Administration",
    "OFFICE OF LOCAL DEFENSE COMMUNITY COOPERATION":
        "Office of Local Defense Community Cooperation",
    "ASSISTANT SECRETARY FOR COMMUNITY PLANNING AND DEVELOPMENT":
        "Assistant Secretary for Community Planning and Development",
    "ENVIRONMENTAL PROTECTION AGENCY": "Environmental Protection Agency",
    "EXECUTIVE OFFICE OF THE PRESIDENT": "Executive Office of the President",
    "DEPT OF THE ARMY": "Department of the Army",
    "U.S. CITIZENSHIP AND IMMIGRATION SERVICES":
        "U.S. Citizenship and Immigration Services",
    "UNIFORMED SERVICES UNIVERSITY OF THE HEALTH SCIENCES  (USUHS)":
        "Uniformed Services University of the Health Sciences  (USUHS)",
    "FOOD AND DRUG ADMINISTRATION": "Food and Drug Administration",
    "BUREAU OF OCEAN ENERGY MANAGEMENT": "Bureau of Ocean Energy Management",
    "OFFICE OF HUMAN RESOURCES AND ADMINISTRATION":
        "Office of Human Resources and Administration",
    "EXPORT-IMPORT BANK OF THE U.S.": "Export-Import Bank of the U.S.",
    "BUREAU OF LABOR STATISTICS": "Bureau of Labor Statistics",
    "ASSISTANT SECRETARY FOR POLICY DEVELOPMENT AND RESEARCH":
        "Assistant Secretary for Policy Development and Research",
    "NATIONAL HIGHWAY TRAFFIC SAFETY ADMINISTRATION":
        "National Highway Traffic Safety Administration",
    "HEALTH RESOURCES AND SERVICES ADMINISTRATION":
        "Health Resources and Services Administration",
    "OFFICE OF THE COORDINATOR FOR CYBER ISSUES":
        "Office of the Coordinator for Cyber Issues",
    "EMPLOYMENT AND TRAINING ADMINISTRATION":
        "Employment and Training Administration",
    "FEDERAL COMMUNICATIONS COMMISSION": "Federal Communications Commission",
    "OFFICE OF DISABILITY EMPLOYMENT POLICY":
        "Office of Disability Employment Policy",
    "ENERGY, DEPARTMENT OF": "Department of Energy",
    "DENALI COMMISSION": "Denali Commission",
    "BUREAU OF RECLAMATION": "Bureau of Reclamation",
    "FOOD AND NUTRITION SERVICE": "Food and Nutrition Service",
    "NATIONAL PARK SERVICE": "National Park Service",
    "CENTERS FOR MEDICARE AND MEDICAID SERVICES":
        "Centers for Medicare and Medicaid Services",
    "OFFICE OF LABOR-MANAGEMENT STANDARDS":
        "Office of Labor-Management Standards",
    "SCIENCE AND TECHNOLOGY": "Science and Technology",
    "INTERNAL REVENUE SERVICE": "Internal Revenue Service",
    "NORTHERN BORDER REGIONAL COMMISSION":
        "Northern Border Regional Commission",
    "COMMUNITY DEVELOPMENT FINANCIAL INSTITUTIONS":
        "Community Development Financial Institutions",
    "AGRICULTURAL RESEARCH SERVICE": "Agricultural Research Service",
    "FEDERAL MEDIATION AND CONCILIATION SERVICE":
        "Federal Mediation and Conciliation Service",
    "OFFICE OF JUSTICE PROGRAMS": "Office of Justice Programs",
    "RAILROAD RETIREMENT BOARD": "Railroad Retirement Board",
    "AGRICULTURE, DEPARTMENT OF": "Department of Agriculture",
    "CORPORATION FOR NATIONAL AND COMMUNITY SERVICE":
        "Corporation for National and Community Service",
    "DEFENSE POW/MIA OFFICE": "Defense POW / MIA Office",
    "DEFENSE SECURITY COOPERATION AGENCY":
        "Defense Security Cooperation Agency",
    "FEDERAL MOTOR CARRIER SAFETY ADMINISTRATION":
        "Federal Motor Carrier Safety Administration",
    "INTERIOR, DEPARTMENT OF THE": "Department of the Interior",
    "BUREAU OF INTERNATIONAL LABOR AFFAIRS":
        "Bureau of International Labor Affairs",
    "OFFICE OF FEDERAL STUDENT AID": "Office of Federal Student Aid",
    "UNITED STATES AGENCY FOR GLOBAL MEDIA, BBG":
        "United States Agency for Global Media, BBG",
    "MINORITY BUSINESS DEVELOPMENT AGENCY":
        "Minority Business Development Agency",
    "NNSA": "NNSA",
    "US CENSUS BUREAU": "U.S. Census Bureau",
    "U. S. Census Bureau": "U.S. Census Bureau",
    "FEDERAL HIGHWAY ADMINISTRATION": "Federal Highway Administration",
    "U.S. SECRET SERVICE": "U.S. Secret Service",
    "NATIONAL OCEANIC AND ATMOSPHERIC ADMINISTRATION":
        "National Oceanic and Atmospheric Administration",
    "INTERNATIONAL TRADE ADMINISTRATION": "International Trade Administration",
    "OFFICE OF WORKERS COMPENSATION PROGRAM":
        "Office of Workers Compensation Program",
    "OFFICE OF SURFACE MINING, RECLAMATION AND ENFORCEMENT":
        "Office of Surface Mining, Reclamation and Enforcement",
    "FEDERAL TRANSIT ADMINISTRATION": "Federal Transit Administration",
    "Countering Weapons of Mass Destruction":
        "Countering Weapons of Mass Destruction",
    "Cybersecurity and Infrastructure Security Agency":
        "Cybersecurity and Infrastructure Security Agency",
    "FOOD SAFETY AND INSPECTION SERVICE": "Food Safety and Inspection Service",
    "BUREAU OF ECONOMIC AND BUSINESS AFFAIRS":
        "Bureau of Economic and Business Affairs",
    "NATIONAL SECURITY AGENCY/CENTRAL SECURITY SERVICE":
        "National Security Agency / Central Security Service",
    "BUREAU OF INDIAN AFFAIRS": "Bureau of Indian Affairs",
    "ASST SECRETARY FOR HOUSING--FEDERAL HOUSING COMMISSIONER":
        "Assistant Secretary for Housing -- Federal Housing Commissioner",
    "HOUSING AND URBAN DEVELOPMENT, DEPARTMENT OF":
        "Department of Housing and Urban Development",
    "USDA, Office of Partnerships and Public Engagement":
        "Office of Partnerships and Public Engagement",
    "DIRECTORY/NATIONAL CEMETERY ADMINISTRATION":
        "Directory / National Cemetery Administration",
    "DEPARTMENTAL OFFICES": "Departmental Offices",
    "VA HEALTH ADMINISTRATION CENTER": "VA Health Administration Center",
    "NATURAL RESOURCES CONSERVATION SERVICE":
        "Natural Resources Conservation Service",
    "APPALACHIAN REGIONAL COMMISSION": "Appalachian Regional Commission",
    "IMMEDIATE OFFICE OF THE SECRETARY OF AGRICULTURE":
        "Immediate Office of the Secretary of Agriculture",
    "RISK MANAGEMENT AGENCY": "Risk Management Agency",
    "INTER-AMERICAN FOUNDATION": "Inter-American Foundation",
    "ASSISTANT SECRETARY FOR FAIR HOUSING AND EQUAL OPPORTUNITY":
        "Assistant Secretary for Fair Housing and Equal Opportunity",
    "GULF COAST ECOSYSTEM RESTORATION COUNCIL":
        "Gulf Coast Ecosystem Restoration Council",
    "OCCUPATIONAL SAFETY AND HEALTH ADMINISTRATION":
        "Occupational Safety and Health Administration",
    "HEALTH AND HUMAN SERVICES, DEPARTMENT OF":
        "Department of Health and Human Services",
    "MORRIS K. UDALL SCHOLARSHIP AND EXCELLENCE "
        "IN NATIONAL ENVIRONMENTAL POLICY FOUNDATION":
            "Morris K. Udall Scholarship and Excellence "
            "in National Environmental Policy Foundation",
    "POLITICAL MILITARY AFFAIRS/ WEAPONS REMOVAL AND ABATEMENT":
        "Political Military Affairs / Weapons Removal and Abatement",
    "ASSISTANT SECRETARY FOR PUBLIC AND INDIAN HOUSING":
        "Assistant Secretary for Public and Indian Housing",
    "CENTERS FOR DISEASE CONTROL AND PREVENTION":
        "Centers for Disease Control and Prevention",
    "ECONOMIC RESEARCH SERVICE": "Economic Research Service",
    "PIPELINE AND HAZARDOUS MATERIALS SAFETY ADMINISTRATION":
        "Pipeline and Hazardous Materials Safety Administration",
    "BUREAU OF INTERNATIONAL SECURITY AND NONPROLIFERATION":
        "Bureau of International Security and Nonproliferation",
    "OFFICE TO MONITOR AND COMBAT TRAFFICKING IN PERSONS":
        "Office to Monitor and Combat Trafficking in Persons",
    "HOMELAND SECURITY, DEPARTMENT OF": "Department of Homeland Security",
    "OFFICE OF U.S. GLOBAL AIDS COORDINATOR":
        "Office of U.S. Global Aids Coordinator",
    "NATIONAL ENDOWMENT FOR THE HUMANITIES":
        "National Endowment for the Humanities",
    "FEDERAL PRISON SYSTEM / BUREAU OF PRISONS":
        "Federal Prison System / Bureau of Prisons",
    "NATIONAL INSTITUTES OF HEALTH": "National Institutes of Health",
    "DEFENSE ADVANCED RESEARCH PROJECTS AGENCY  (DARPA)":
        "Defense Advanced Research Projects Agency  (DARPA)",
    "NATIONAL AGRICULTURAL STATISTICS SERVICE":
        "National Agricultural Statistics Service",
    "FEDERAL FINANCIAL INSTITUTIONS EXAMINATION COUNCIL "
        "APPRAISAL SUBCOMMITTEE":
            "Federal Financial Institutions Examination Council "
            "Appraisal Subcommittee",
    "BUREAU OF LAND MANAGEMENT": "Bureau of Land Management",
    "FEDERAL EMERGENCY MANAGEMENT AGENCY":
        "Federal Emergency Management Agency",
    "TREASURY, DEPARTMENT OF THE": "Department of the Treasury",
    "NATIONAL TELECOMMUNICATIONS AND INFORMATION ADMINISTRATION":
        "National Telecommunications and Information Administration",
    "BARRY GOLDWATER SCHOLARSHIP AND EXCELLENCE IN EDUCATION FUND":
        "Barry Goldwater Scholarship and Excellence in Education Fund",
    "DEFENSE INTELLIGENCE AGENCY": "Defense Intelligence Agency",
    "OFFICE OF THE COORDINATOR OF U.S. ASSISTANCE TO EUROPE AND EURASIA":
        "Office of the Coordinator of U.S. Assistance to Europe and Eurasia",
    "NATIONAL SCIENCE FOUNDATION": "National Science Foundation",
    "WASHINGTON HEADQUARTERS SERVICES (WHS)":
        "Washington Headquarters Services (WHS)",
    "AGRICULTURAL MARKETING SERVICE": "Agricultural Marketing Service",
    "OFFICES, BOARDS AND DIVISIONS": "Boards and Divisions Offices",
    "UNITED STATES INSTITUTE OF PEACE": "United States Institute of Peace",
    "SOCIAL SECURITY ADMINISTRATION": "Social Security Administration",
    "OFFICE OF THE SECRETARY": "Office of the Secretary",
    "FEDERAL PERMITTING IMPROVEMENT STEERING COUNCIL":
        "Federal Permitting Improvement Steering Council",
    "VETERANS EMPLOYMENT AND TRAINING SERVICES":
        "Veterans Employment and Training Services",
    "LIBRARY OF CONGRESS": "Library of Congress",
    "JUSTICE, DEPARTMENT OF": "Department of Justice",
    "Inter-American Foundation": "Inter-American Foundation",
    "DEPT OF DEFENSE EDUCATION ACTIVITY (DODEA)":
        "Department of Defense Education Activity (DODEA)",
    "National Council on Disability": "National Council on Disability",
    "OFFICE OF LEAD HAZARD CONTROL AND HEALTHY HOMES":
        "Office of Lead Hazard Control and Healthy Homes",
    "IMMED OFFICE OF THE SECRETARY OF HEALTH AND HUMAN SERVICES":
        "Immed Office of the Secretary of Health and Human Services",
    "COMMERCE, DEPARTMENT OF": "Department of Commerce",
    "MARITIME ADMINISTRATION": "Maritime Administration",
    "UNITED STATES INTERNATIONAL DEVELOPMENT FINANCE CORPORATION":
        "United States International Development Finance Corporation"
}

ASSISTANCE_TYPE_DISPLAY_NAMES = {
    "FORMULA GRANTS": "Formula Grants",
    "PROJECT GRANTS": "Project Grants",
    "DIRECT PAYMENTS FOR A SPECIFIED USE":
        "Direct Payments for a Specified Use",
    "DIRECT PAYMENTS WITH UNRESTRICTED USE":
        "Direct Payments with Unrestricted Use",
    "DIRECT LOANS": "Direct Loans",
    "GUARANTEED/INSURED LOANS": "Guaranteed / Insured Loans",
    "INSURANCE": "Insurance",
    "SALE, EXCHANGE, OR DONATION OF PROPERTY OR GOODS":
        "Sale, Exchange, or Donation of Property or Goods",
    "USE OF PROPERTY, FACILITIES, OR EQUIPMENT":
        "Use of Property, Facilities, or Equipment",
    "PROVISION OF SPECIALIZED SERVICES": "Provision of Specialized Services",
    "ADVISORY SERVICES AND COUNSELING": "Advisory Services and Counseling",
    "DISSEMINATION OF TECHNICAL INFORMATION":
        "Dissemination of Technical Information",
    "TRAINING": "Training",
    "INVESTIGATION OF COMPLAINTS": "Investigation of Complaints",
    "FEDERAL EMPLOYMENT": "Federal Employment",
    "SALARIES AND EXPENSES": "Salaries and Expenses"
}

CFO_ACT_AGENCY_NAMES = [
    "Agency for International Development",
    "Department of Agriculture",
    "Department of Commerce",
    "Department of Defense",
    "Department of Education",
    "Department of Energy",
    "Department of Health and Human Services",
    "Department of Homeland Security",
    "Department of Housing and Urban Development",
    "Department of the Interior",
    "Department of Justice",
    "Department of Labor",
    "Department of State",
    "Department of Transportation",
    "Department of the Treasury",
    "Department of Veterans Affairs",
    "Environmental Protection Agency",
    "General Services Administration",
    "National Aeronautics and Space Administration",
    "National Science Foundation",
    "Nuclear Regulatory Commission",
    "Office of Personnel Management",
    "Small Business Administration",
    "Social Security Administration"
]

PROGRAM_TYPE_MAPPING = {
    "tax_expenditure": "Tax Expenditures",
    "assistance_listing": "Federal Financial Assistance",
    "interest": "Interest on the Public Debt",
    "government_service": "Government Service",
    "acquisition_contract": "Acquisition Contract"
}
