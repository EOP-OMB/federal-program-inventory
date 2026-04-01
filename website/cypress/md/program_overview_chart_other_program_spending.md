---
layout: default
title: Program Overview Visualization
outlays: '[{"x":"2015","outlays":22,"forgone_revenue":20},{"x":"2015","outlays":24,"forgone_revenue":22},{"x":"2017","outlays":24,"forgone_revenue":24},{"x":"2018","outlays":26,"forgone_revenue":26},{"x":"2019","outlays":28,"forgone_revenue":20},{"x":"2020","outlays":30,"forgone_revenue":30},{"x":"2021","outlays":34,"forgone_revenue":34},{"x":"2022","outlays":38,"forgone_revenue":38},{"x":"2023","outlays":42,"forgone_revenue":45},{"x":"2024","outlays":47,"forgone_revenue":52},{"x":"2025","outlays":50,"forgone_revenue":60}]'
---

<h3 id="chart-header" class="font-sans-xs">Outlays by Fiscal Year</h3>
<div class="grid grid-row radius-md">
    <div class="grid-col-12">
        <div id="chart" style="width:100%" data-outlays='{{ page.outlays }}'></div>
        <p id="no-chart" class="hide">Expenditures not yet available.</p>
    </div>
</div>
{% include scripts/_chart-utils.html %}
{% include scripts/_tab-navigation.html %}
{% include scripts/_program-charts.html %}