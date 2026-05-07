---
layout: default
title: Improper Payments Seection
improper_payments:
- agency: SSA
  end_date: 09-2024
  fiscal_year: 2025
  improper_payments: 1617.09514973
  insufficient_payment: 0.0
  name: Old-Age and Survivors Insurance (OASI)
  outlays: 1287478.74951543
  slug: ssa-old-age-and-survivors-insurance-oasi
  start_date: 10-2023
improper_payments_is_multiple: false
improper_payments_related_programs:
- id: '96.004'
  name: Social Security Survivors Insurance
  permalink: /program/96.004
---

<div id="improper-payment" style="margin: 10%;">
  {% include components/_improper-payment-section.html
    improper_payments=page.improper_payments
    improper_payments_is_multiple=page.improper_payments_is_multiple
    improper_payments_related_programs=page.improper_payments_related_programs %}
</div>
{% include scripts/_dollar-standardization.html %}