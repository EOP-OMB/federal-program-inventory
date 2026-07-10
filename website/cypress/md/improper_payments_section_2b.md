---
layout: default
title: Improper Payments Seection
improper_payments:
- agency: USDA
  end_date: ''
  fiscal_year: 2025
  improper_payments: 0.0
  insufficient_payment: 0.0
  name: Salaries & Expenses
  outlays: 0.0
  slug: null
  start_date: ''
improper_payments_is_multiple: false
improper_payments_related_programs:
- id: '10.253'
  name: Consumer Data and Nutrition Research
  permalink: /program/10.253
- id: '10.255'
  name: Research Innovation and Development Grants in Economic (RIDGE)
  permalink: /program/10.255
- id: '10.951'
  name: Census of Agriculture
  permalink: /program/10.951
---

<div id="improper-payment" style="margin: 10%;">
  {% include components/_improper-payment-section.html
    improper_payments=page.improper_payments
    improper_payments_is_multiple=page.improper_payments_is_multiple
    improper_payments_related_programs=page.improper_payments_related_programs %}
</div>
{% include scripts/_dollar-standardization.html %}