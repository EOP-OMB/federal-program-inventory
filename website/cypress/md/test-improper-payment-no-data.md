---
layout: default
title: Test - Improper Payment Card (No Data)
permalink: /test-improper-payment-no-data.html
improper_payments: null
outlays: '[{"x":"2025","outlay":50000000.0,"obligation":60000000.0}]'
---

{% include scripts/_dollar-standardization.html %}

<div class="grid-container">
  <div class="grid-row grid-gap">
    <div class="grid-col-12 margin-bottom-5">
      <h1>Test Page - Improper Payment Card (No Data)</h1>
      <p>This page tests the improper payment card when there is no improper payment data (should not display).</p>
      {% include components/_improper-payment.html %}
    </div>
  </div>
</div>