---
layout: default
---

<div class="grid-container">
  <div class="grid-row grid-gap">
    <div class="grid-col-9 margin-bottom-5 border-top border-base-lightest">
      {% include components/_insight-section.html
        program_number=1
        expenditure_total="$123"
        largest_program_link="/test/large"
        largest_program_title="Large Program"
        largest_program_expenditure="$10"
        smallest_program_link="/test/small"
        smallest_program_title="Small Program"
        smallest_program_expenditure="$1"
      %}
    </div>
  </div>
</div>
