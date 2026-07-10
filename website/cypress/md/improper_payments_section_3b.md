---
layout: default
title: Improper Payments Seection
improper_payments:
- agency: HHS
  end_date: ''
  fiscal_year: 2025
  improper_payments: 0.0
  insufficient_payment: 0.0
  name: Centers for Medicare & Medicaid Services (CMS) - ACO REACH (Medicare Part
    B)
  outlays: 0.0
  slug: null
  start_date: ''
- agency: HHS
  end_date: ''
  fiscal_year: 2025
  improper_payments: 0.0
  insufficient_payment: 0.0
  name: Centers for Medicare & Medicaid Services (CMS) - ESRD Networks
  outlays: 0.0
  slug: null
  start_date: ''
- agency: HHS
  end_date: ''
  fiscal_year: 2025
  improper_payments: 0.0
  insufficient_payment: 0.0
  name: Centers for Medicare & Medicaid Services (CMS) - Kidney Care Choices (Benefits)
  outlays: 0.0
  slug: null
  start_date: ''
- agency: HHS
  end_date: ''
  fiscal_year: 2025
  improper_payments: 0.0
  insufficient_payment: 0.0
  name: Centers for Medicare & Medicaid Services (CMS) - Maryland Total Cost of Care
    (Benefits)
  outlays: 0.0
  slug: null
  start_date: ''
- agency: HHS
  end_date: 12-2023
  fiscal_year: 2025
  improper_payments: 23665.12
  insufficient_payment: 0.0
  name: Centers for Medicare & Medicaid Services (CMS) - Medicare Advantage (Part
    C)
  outlays: 388716.84
  slug: hhs-centers-for-medicare-medicaid-services-cms-medicare-adva-ef65c066
  start_date: 01-2023
- agency: HHS
  end_date: 06-2024
  fiscal_year: 2025
  improper_payments: 28826.5867
  insufficient_payment: 0.0
  name: Centers for Medicare & Medicaid Services (CMS) - Medicare Fee-for-Service
    (FFS)
  outlays: 439878.6927
  slug: hhs-centers-for-medicare-medicaid-services-cms-medicare-fee--db617d96
  start_date: 07-2023
- agency: HHS
  end_date: ''
  fiscal_year: 2025
  improper_payments: 0.0
  insufficient_payment: 0.0
  name: Centers for Medicare & Medicaid Services (CMS) - Medicare Independence at
    Home (Benefits)
  outlays: 0.0
  slug: null
  start_date: ''
- agency: HHS
  end_date: ''
  fiscal_year: 2025
  improper_payments: 0.0
  insufficient_payment: 0.0
  name: Centers for Medicare & Medicaid Services (CMS) - Medicare Shared Savings (Supplementary
    Medical Insurance)
  outlays: 0.0
  slug: null
  start_date: ''
- agency: HHS
  end_date: ''
  fiscal_year: 2025
  improper_payments: 0.0
  insufficient_payment: 0.0
  name: Centers for Medicare & Medicaid Services (CMS) - Oncology Care Model (Benefits)
  outlays: 0.0
  slug: null
  start_date: ''
- agency: HHS
  end_date: ''
  fiscal_year: 2025
  improper_payments: 0.0
  insufficient_payment: 0.0
  name: Centers for Medicare & Medicaid Services (CMS) - Over the Counter COVID-19
    Test Benefits
  outlays: 0.0
  slug: null
  start_date: ''
- agency: HHS
  end_date: ''
  fiscal_year: 2025
  improper_payments: 0.0
  insufficient_payment: 0.0
  name: Centers for Medicare & Medicaid Services (CMS) - Primary Care First (Benefits)
  outlays: 0.0
  slug: null
  start_date: ''
- agency: HHS
  end_date: null
  fiscal_year: '2025'
  improper_payments: null
  insufficient_payment: null
  name: Centers for Medicare & Medicaid Services (CMS) - Primary Care First Model
    Options
  outlays: null
  slug: null
  start_date: null
improper_payments_is_multiple: true
improper_payments_related_programs:
- id: '57.006'
  name: Social Insurance for Railroad Workers
  permalink: /program/57.006
- id: '93.773'
  name: Medicare Hospital Insurance
  permalink: /program/93.773
---

<div id="improper-payment" style="margin: 10%;">
  {% include components/_improper-payment-section.html
    improper_payments=page.improper_payments
    improper_payments_is_multiple=page.improper_payments_is_multiple
    improper_payments_related_programs=page.improper_payments_related_programs %}
</div>
{% include scripts/_dollar-standardization.html %}