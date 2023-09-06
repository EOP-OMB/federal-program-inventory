import requests

# fetch the standard SAM.gov dictionary
r = requests.get('https://sam.gov/api/prod/fac/v1/programs/dictionaries?ids=match_percent,assistance_type,applicant_types,assistance_usage_types,beneficiary_types,cfr200_requirements&size=&filterElementIds=&keyword=')

# save the JSON of the 
with open('source_files/dictionary.json', 'w') as file:
    file.write(r.text)