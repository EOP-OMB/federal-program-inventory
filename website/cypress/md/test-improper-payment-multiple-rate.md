---
layout: default
title: Test - Improper Payment Card (Multiple Rates)
permalink: /test-improper-payment-multiple-rate.html
improper_payments:
- name: Test Payment Program Activity 1
  outlays: 50000000
  improper_payments: 7500000
  start_date: 10-2024
  end_date: 12-2024
- name: Test Payment Program Activity 1
  outlays: 60000000
  improper_payments: 12000000
  start_date: 01-2025
  end_date: 03-2025
improper_payments_total: 19500000.0
improper_payments_percent: 17.5
improper_payments_is_multiple: true
headline_amount: 125000000.0
outlays: '[{"x":"2025","outlay":125000000.0,"obligation":110000000.0}]'
---

{% include scripts/_dollar-standardization.html %}

<div class="grid-container">
  <div class="grid-row grid-gap">
    <div class="grid-col-12 margin-bottom-5">
      <h1>Test Page - Improper Payment Card (Multiple Rates)</h1>
      <p>This page tests the improper payment card when improper_payments_is_multiple is true. The card should display "Rate: Multiple" and "Amount: Varies" to indicate that this program has multiple improper payment program activities with different rate timeframes.</p>
      {% include components/_improper-payment.html %}
    </div>
  </div>
</div>
