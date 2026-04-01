---
layout: default
title: Program Spending Visualization
outlays: '[{"x":"2017","outlay":85,"obligation":145},{"x":"2018","outlay":65,"obligation":215},{"x":"2019","outlay":50,"obligation":315},{"x":"2021","outlay":380,"obligation":400},{"x":"2022","outlay":460,"obligation":490},{"x":"2023","outlay":510,"obligation":530},{"x":"2024","outlay":580,"obligation":610},{"x":"2025","outlay":550,"obligation":580}]'
---

<h3 id="chart-header" class="font-sans-xs">Spending</h3>
{% include components/_spending-chart.html
    outlays=page.outlays %}
{% include scripts/_chart-utils.html %}
{% include scripts/_tab-navigation.html %}
{% include scripts/_program-charts.html %}