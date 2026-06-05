---
layout: default
authorizations:
- text: Test auth with link
  url: https://www.govinfo.gov/link/statute/88/1305
- text: Social Security Act of 1935, Provides authorization and basis for paying social
    security benefits for American workers and certain family members.. 49 Stat. 620.
    Pub. L. 74, 271. 42 U.S.C. &sect; 7.
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