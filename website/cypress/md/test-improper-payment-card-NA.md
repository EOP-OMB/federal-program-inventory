---
layout: default
title: Test - Improper Payment Card (N/A)
permalink: /test-improper-payment-card-NA.html
improper_payments: null
headline_amount: 50000000.0
outlays: '[{"x":"2025","outlay":50000000.0,"obligation":60000000.0}]'
---

{% include scripts/_dollar-standardization.html %}

<div class="grid-container">
  <div class="grid-row grid-gap">
    <div class="grid-col-12 margin-bottom-5">
      <h1>Test Page - Improper Payment Card (N/A)</h1>
      <p>This page tests the improper payment card when improper payment data is not available, showing N/A values in a grayed out box.</p>
      {% include components/_improper-payment.html %}
    </div>
  </div>
</div>