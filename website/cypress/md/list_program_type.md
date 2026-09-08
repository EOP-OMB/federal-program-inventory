---
layout: default
assistance_types:
  - Direct Payments with Unrestricted Use
---

<div class="grid-container">
  <div class="grid-row grid-gap">
    <div class="grid-col-9 margin-bottom-5 border-top border-base-lightest">
      {% include components/_list-section.html 
         title="Program Type" 
         title_weight="text-bold"
         items=page.assistance_types 
         icon="assessment" 
         margin_class="margin-bottom-2"
         data_filter_type="assistance"
         icon_class="margin-right-1" %}
    </div>
  </div>
</div>
{% include footers/_footer-program.html %}