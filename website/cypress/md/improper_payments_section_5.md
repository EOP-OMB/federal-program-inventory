---
layout: default
title: Improper Payments Seection
improper_payments: []
improper_payments_is_multiple: false
improper_payments_percent: 0
improper_payments_related_programs: []
---

<div id="improper-payment" style="margin: 10%;">
  {% include components/_improper-payment-section.html
    improper_payments=page.improper_payments
    improper_payments_is_multiple=page.improper_payments_is_multiple
    improper_payments_related_programs=page.improper_payments_related_programs %}
</div>
{% include scripts/_dollar-standardization.html %}