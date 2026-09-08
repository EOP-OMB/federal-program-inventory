---
layout: default
title: Program Spending Visualization
outlays: '[]'
---

<h3 id="chart-header" class="font-sans-xs">Spending</h3>
{% include components/_spending-chart.html
    outlays=page.outlays
    program_type='assistance_listing' %}
{% include scripts/_chart-utils.html %}
{% include scripts/_tab-navigation.html %}
{% include scripts/_program-charts.html %}