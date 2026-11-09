---
layout: default
title: Taxonomy filter scenarios
categories:
- title: Education
  sub_categories:
  - title: K-12 Education
  - title: Post-Secondary Education
- title: Health
  sub_categories:
  - title: Healthcare Access
- title: Unmapped Category
  sub_categories:
  - title: Unmapped Sub
pfa_options:
- title: Alpha Objective
  definition: First government-wide objective.
  permalink: /gwo/GWO_ALPHA
- title: Bravo Objective
  definition: Second government-wide objective.
  permalink: /gwo/GWO_BRAVO
- title: Charlie Objective
  definition: Third government-wide objective.
  permalink: /gwo/GWO_CHARLIE
- title: Delta Unmapped Objective
  definition: Objective with no program mapping.
  permalink: ''
- title: Echo Objective
  definition: Pagination filler echo.
  permalink: /gwo/GWO_ECHO
- title: Foxtrot Objective
  definition: Pagination filler foxtrot.
  permalink: /gwo/GWO_FOXTROT
- title: Golf Objective
  definition: Pagination filler golf.
  permalink: /gwo/GWO_GOLF
- title: Hotel Objective
  definition: Pagination filler hotel.
  permalink: /gwo/GWO_HOTEL
- title: India Objective
  definition: Pagination filler india.
  permalink: /gwo/GWO_INDIA
- title: Juliet Objective
  definition: Pagination filler juliet.
  permalink: /gwo/GWO_JULIET
- title: Kilo Objective
  definition: Pagination filler kilo.
  permalink: /gwo/GWO_KILO
- title: Lima Objective
  definition: Pagination filler lima.
  permalink: /gwo/GWO_LIMA
program_pfa:
- category: Education
  subcategory: K-12 Education
  pfa: Alpha Objective
- category: Education
  subcategory: K-12 Education
  pfa: Bravo Objective
- category: Health
  subcategory: Healthcare Access
  pfa: Charlie Objective
---

<div class="grid-container margin-bottom-5">
  {% include components/_taxonomy-section.html %}
</div>

<script>
  (function replaceTaxonomyProgramSource() {
    const source = document.getElementById('taxonomy-program-pfa-source');
    if (!source) {
      return;
    }
    source.innerHTML = `{% for mapping in page.program_pfa %}<span data-category="{{ mapping.category | escape }}" data-subcategory="{{ mapping.subcategory | escape }}" data-pfa="{{ mapping.pfa | escape }}"></span>{% endfor %}`;
  })();
</script>
<script src="/assets/js/taxonomy-filter-table.js"></script>
