---
layout: default
title: Improper Payments Seection
improper_payments:
- agency: SBA
  end_date: null
  fiscal_year: '2025'
  improper_payments: null
  insufficient_payment: null
  name: Paycheck Protection Program (PPP) Loan Approvals
  outlays: null
  slug: sba-paycheck-protection-program-ppp-loan-approvals
  start_date: null
- agency: SBA
  end_date: null
  fiscal_year: 2025
  improper_payments: null
  insufficient_payment: null
  name: Paycheck Protection Program (PPP) Loan Forgiveness
  outlays: null
  slug: sba-paycheck-protection-program-ppp-loan-forgiveness
  start_date: null
- agency: SBA
  end_date: null
  fiscal_year: 2025
  improper_payments: null
  insufficient_payment: null
  name: Paycheck Protection Program (PPP) Loan Guaranty Purchases
  outlays: null
  slug: sba-paycheck-protection-program-ppp-loan-guaranty-purchases
  start_date: 04-2024
improper_payments_is_multiple: false
improper_payments_related_programs: []
---

<div id="improper-payment" style="margin: 10%;">
  {% include components/_improper-payment-section.html
    improper_payments=page.improper_payments
    improper_payments_is_multiple=page.improper_payments_is_multiple
    improper_payments_related_programs=page.improper_payments_related_programs %}
</div>
{% include scripts/_dollar-standardization.html %}