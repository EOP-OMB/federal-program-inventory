---
layout: default
beneficiary_types:
  - Child (6-15)
  - Individual/Family
---

<div class="grid-container">
  <div class="grid-row grid-gap">
    <div class="grid-col-9 margin-bottom-5 border-top border-base-lightest">
      {% include components/_list-section.html
         title="Beneficiaries"
         title_weight="text-bold"
         items=page.beneficiary_types
         icon="person"
         icon_style="min-width: 1rem; width: 1rem; height: 1rem;"
         span_class="flex-fill" %}
    </div>
  </div>
</div>
{% include footers/_footer-program.html %}