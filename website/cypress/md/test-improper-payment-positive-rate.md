---
layout: default
title: Test - Improper Payment Card (Positive Rate)
permalink: /test-improper-payment-positive-rate.html
improper_payments:
- name: Test Payment Program
  outlays: 100000000
  improper_payments: 15000000
improper_payments_total: 15000000.0
improper_payments_percent: 15.0
headline_amount: 75000000.0
outlays: '[{"x":"2025","outlay":75000000.0,"obligation":80000000.0}]'
---

{% include scripts/_dollar-standardization.html %}

<div class="grid-container">
  <div class="grid-row grid-gap">
    <div class="grid-col-12 margin-bottom-5">
      <h1>Test Page - Improper Payment Card (Positive Rate)</h1>
      <p>This page tests the improper payment card with a positive (15%) improper payment rate.</p>
      {% include components/_improper-payment.html %}
    </div>
  </div>
</div>