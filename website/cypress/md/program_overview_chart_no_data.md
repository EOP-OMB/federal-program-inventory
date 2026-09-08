---
layout: default
title: Program Overview Visualization
outlays: '[{"x":"2023","obligation":0.0,"outlay":0.0},{"x":"2024","obligation":0.0,"outlay":0.0},{"x":"2025","obligation":0.0,"outlay":0.0}]'
---

<h3 id="chart-header" class="font-sans-xs">Outlays by Fiscal Year</h3>
<div class="grid grid-row radius-md">
    <div class="grid-col-12">
        <div id="chart" style="width:100%" data-outlays='{{ page.outlays }}' data-program-type='assistance_listing'></div>
        <p id="no-chart" class="hide">Expenditures not yet available.</p>
    </div>
</div>
{% include scripts/_chart-utils.html %}
{% include scripts/_tab-navigation.html %}
{% include scripts/_program-charts.html %}