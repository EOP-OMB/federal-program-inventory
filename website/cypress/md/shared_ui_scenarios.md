---
layout: default
title: Shared UI scenarios
table_rows:
- name: Zebra Program
  agency: Agency Z
  expenditure_amount: 100
  permalink: /test/index.html
- name: Alpha Program
  agency: Agency A
  expenditure_amount: 300
  permalink: /test/index.html
- name: Mid Program
  agency: Agency M
  expenditure_amount: 200
  permalink: /test/index.html
---

<div class="grid-container padding-y-4">
  <section id="tooltip-section" class="margin-bottom-5">
    <h2>Tooltip</h2>
    {% capture tip_html %}
      Scenario tooltip with a
      <a href="https://www.usaspending.gov">USAspending.gov</a>
      link.
    {% endcapture %}
    {% include components/_custom-tooltip.html
      id="shared-ui-tip"
      trigger_text="More info"
      content=tip_html %}
  </section>

  <section id="external-link-section" class="margin-bottom-5">
    <h2>External link</h2>
    {% include components/_external-link.html
      href="https://www.usaspending.gov"
      text="USAspending.gov" %}
  </section>

  <section id="sortable-table-section">
    <h2>Sortable table</h2>
    {% assign table_columns = "name,agency,expenditure_amount" | split: "," %}
    {% assign table_labels = "Program,Agency,Amount" | split: "," %}
    {% assign table_widths = "40%,30%,30%" | split: "," %}
    {% assign table_alignments = "left,left,right" | split: "," %}
    {% assign table_types = "text,text,currency" | split: "," %}
    {% assign table_bold = "true,false,true" | split: "," %}
    {% include components/_sortable-table.html
      data=page.table_rows
      columns=table_columns
      labels=table_labels
      widths=table_widths
      alignments=table_alignments
      types=table_types
      bold=table_bold
      show_total=true
      total_value=600
      clickable=true
      permalink_field="permalink" %}
  </section>
</div>

{% include scripts/_table-utils.html %}
