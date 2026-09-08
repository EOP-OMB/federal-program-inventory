---
layout: default
authorizations: []
rules_regulations: 'Test rule'
---

<div class="grid-container">
  <div class="grid-row">
    <div class="grid-col-12">
      {% include components/_authorization-tab.html
        authorizations=page.authorizations
        rules_regulations=page.rules_regulations%}
    </div>
  </div>
</div>