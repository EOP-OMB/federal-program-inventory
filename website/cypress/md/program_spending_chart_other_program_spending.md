---
layout: default
title: Program Spending Visualization
outlays: '[{"x":"2015","outlays":35,"forgone_revenue":70},{"x":"2016","outlays":100.69,"forgone_revenue":240},{"x":"2017","outlays":85,"forgone_revenue":145},{"x":"2018","outlays":65,"forgone_revenue":215},{"x":"2019","outlays":50,"forgone_revenue":315},{"x":"2020","outlays":310,"forgone_revenue":340},{"x":"2021","outlays":380,"forgone_revenue":400},{"x":"2022","outlays":460,"forgone_revenue":490},{"x":"2023","outlays":510,"forgone_revenue":530},{"x":"2024","outlays":580,"forgone_revenue":610},{"x":"2025","outlays":550,"forgone_revenue":580}]'
---

<h3 id="chart-header" class="font-sans-xs">Spending</h3>
{% include components/_spending-chart.html
    outlays=page.outlays
    program_type='tax_expenditure' %}
{% include scripts/_chart-utils.html %}
{% include scripts/_tab-navigation.html %}
{% include scripts/_program-charts.html %}