---
layout: default
applicant_types:
  - Individual/Family
  - Federal
---

<div class="grid-container">
  <div class="grid-row grid-gap">
    <div class="grid-col-9 margin-bottom-5 border-top border-base-lightest">
      {% include components/_list-section.html 
         title="Applicants" 
         title_weight="text-bold"
         items=page.applicant_types 
         icon="assessment" 
         margin_class="margin-bottom-2"
         data_filter_type="applicant"
         icon_class="margin-right-1" %}
    </div>
  </div>
</div>
{% include footers/_footer-program.html %}