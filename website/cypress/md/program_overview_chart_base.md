---
layout: default
title: Program Overview Visualization
outlays: '[{"x":"2015","outlay":22,"obligation":20},{"x":"2015","outlay":24,"obligation":22},{"x":"2017","outlay":24,"obligation":24},{"x":"2018","outlay":26,"obligation":26},{"x":"2019","outlay":28,"obligation":20},{"x":"2020","outlay":30,"obligation":30},{"x":"2021","outlay":34,"obligation":34},{"x":"2022","outlay":38,"obligation":38},{"x":"2023","outlay":42,"obligation":45},{"x":"2024","outlay":47,"obligation":52},{"x":"2025","outlay":50,"obligation":60}]'
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