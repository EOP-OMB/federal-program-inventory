---
layout: default
title: Test - GWO Target Count Card
permalink: /test-gwo-pon-count.html
---

<div class="grid-container">
  <div class="grid-row grid-gap">
    <div class="grid-col-12 margin-bottom-5">
      <h1>Test Page - GWO Target Count Card</h1>
      <p>This page tests that the GWO card target_count value is displayed correctly.</p>
    </div>
  </div>

  <div class="grid-row grid-gap padding-bottom-205">
    <div class="grid-col-4 border-right-2px border-top-2px border-base" style="border-right: 1px dotted #000; border-top: 1px dotted #000;">
      <div class="display-flex flex-justify flex-align-center margin-top-2 margin-bottom-3">
        <h2 class="text-bold">Purpose</h2>
      </div>
      <h4 class="text-base-dark margin-top-1 margin-bottom-2">Government-Wide Outcomes</h4>
      
      <!-- GWO Card with target_count = 5 -->
      <div data-testid="gwo-clickable-tile">
        {% include components/_clickable-tile.html href="/gwo/test" title="Test GWO Card" target_count=5 icon="flag" icon_style="min-width: 1rem; width: 1rem; height: 1rem;" title_margin="margin-bottom-05" padding="" %}
      </div>
    </div>
  </div>
</div>
