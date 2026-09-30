# Manual website tests

Use this checklist on the live Federal Program Inventory at [https://fpi.omb.gov/](https://fpi.omb.gov/). You only need that website plus the public source sites it draws from, especially [SAM.gov](https://sam.gov/) and [USAspending.gov](https://www.usaspending.gov/). Automated tests already cover layout, filters, charts, empty states, and downloads; these steps check that real program data still matches those sources.

## Home (`/`)

- [ ] Open the [homepage](https://fpi.omb.gov/). Confirm the four headline numbers (programs, spending, agencies, and outcomes) are filled in and that the spending figure is labeled for the fiscal year shown on the page.
- [ ] From the homepage, select **Explore programs**. Confirm the next page is Program Search and that it lists real programs rather than an error message.
- [ ] From the homepage, select **About**. Confirm the next page is About the FPI and that it still describes SAM.gov and USAspending.gov as data sources.
- [ ] From the homepage, follow the **Find programs**, **Explore spending**, and **Understand methodology** cards. Confirm they open Program Search, the category spending page, and About the FPI.

## Search (`/search`)

- [ ] Open [Program Search](https://fpi.omb.gov/search) and search for `Supplemental Nutrition Assistance Program` or `SNAP`. Confirm the results include assistance listing **10.551** from the Department of Agriculture’s Food and Nutrition Service.
- [ ] On Program Search, open the Agency filter and choose **Department of Agriculture**. Confirm SNAP (10.551) still appears among USDA programs and that the listed agency name matches [SAM.gov](https://sam.gov/).
- [ ] Open SNAP from the search results and compare its latest-year spending with the same assistance listing on [USAspending.gov](https://www.usaspending.gov/). Confirm the amount is in the same ballpark (exact dollars may differ because of pull dates).

## Category index (`/category`)

- [ ] Open [Explore spending](https://fpi.omb.gov/category). Confirm the page names the current fiscal year, mentions SAM.gov and USAspending.gov as sources, and shows **Food and Nutrition** among the categories.
- [ ] On the category index, choose **Food and Nutrition** and select **Update category**. Confirm you land on the Food and Nutrition category page rather than staying on the all-categories view.

## Category (`/category/<category>`)

- [ ] Open the [Food and Nutrition](https://fpi.omb.gov/category/food-and-nutrition) category page. Confirm the program count and fiscal-year spending total are populated, and that **Department of Agriculture** appears among the agencies.
- [ ] On that category page, find **Food and Nutrition Assistance** in the sub-category list or dropdown. Confirm it is present and that opening it goes to the matching sub-category page.

## Subcategory (`/category/<category>/<subcategory>`)

- [ ] Open [Food and Nutrition Assistance](https://fpi.omb.gov/category/food-and-nutrition/food-and-nutrition-assistance). Confirm **Supplemental Nutrition Assistance Program (10.551)** appears in the programs table with the Department of Agriculture as the agency.
- [ ] From that sub-category table, open SNAP and compare the title and assistance listing number with the [SNAP listing on SAM.gov](https://sam.gov/fal/b15e4e5eabfc4ee98249fec6d0044d3c/view). Confirm they match.

## About the FPI (`/about/fpi`)

- [ ] Open [About the FPI](https://fpi.omb.gov/about/fpi). Confirm the overview still says the inventory uses SAM.gov, USAspending.gov, and PaymentAccuracy.gov, and that the fiscal-year spending total matches the homepage spending headline.
- [ ] On About the FPI, open the most recent year in **FPI Timeline and Evolution**. Confirm that year describes the same completed fiscal year shown on the homepage and category pages.

## Data, Terms & Concepts (`/about/terms`)

- [ ] Open [Data, Terms & Concepts](https://fpi.omb.gov/about/terms). Confirm the Data Updates list includes a SAM.gov assistance-listings date and a USAspending.gov transaction date.
- [ ] On that page, download the all-program data file. Confirm you can find **Supplemental Nutrition Assistance Program** / **10.551** in the file.

## Taxonomy (`/about/taxonomy`)

- [ ] Open the [FPI Taxonomy](https://fpi.omb.gov/about/taxonomy) page and find **End Hunger**. Confirm the title and definition match the [End Hunger](https://fpi.omb.gov/gwo/GWO_K3) government-wide objective page.
- [ ] On the taxonomy page, limit the table to the **Food and Nutrition** category. Confirm **End Hunger** remains in the results and still links to the same GWO page.

## Program (`/program/<program>`)

- [ ] Open the [Supplemental Nutrition Assistance Program (10.551)](https://fpi.omb.gov/program/10.551) page. Confirm the title, assistance listing number, Department of Agriculture / Food and Nutrition Service, and overview text match the [SNAP listing on SAM.gov](https://sam.gov/fal/b15e4e5eabfc4ee98249fec6d0044d3c/view).
- [ ] On that SNAP page, note the latest fiscal-year spending on the Overview or Spending tab. Confirm it is in the same ballpark as the [SNAP results on USAspending.gov](https://www.usaspending.gov/search/?hash=468b38afca1a160cf891746a1cab58f1).
- [ ] On that SNAP page, open the Spending tab’s improper-payment information. Confirm the program name and rate are consistent with the [SNAP entry on PaymentAccuracy.gov](https://paymentaccuracy.gov/program/usda-supplemental-nutrition-assistance-program).
- [ ] On that SNAP page, check the Purpose section. Confirm the objective is **End Hunger** and that at least one listed outcome is **Improve Availability of Healthy Foods**, and that both links open the matching GWO and PON pages.
- [ ] On that SNAP page, open the Authorization tab. Confirm the authorizing statutes are the same ones shown on the [SNAP listing on SAM.gov](https://sam.gov/fal/b15e4e5eabfc4ee98249fec6d0044d3c/view).

## Government-wide objective (`/gwo/<gwo>`)

- [ ] Open the [End Hunger](https://fpi.omb.gov/gwo/GWO_K3) page. Confirm the definition matches the taxonomy entry for End Hunger, and that **Supplemental Nutrition Assistance Program** appears in the related programs list.
- [ ] On that GWO page, spot-check SNAP’s name, agency, and spending against [SAM.gov](https://sam.gov/fal/b15e4e5eabfc4ee98249fec6d0044d3c/view) and [USAspending.gov](https://www.usaspending.gov/search/?hash=468b38afca1a160cf891746a1cab58f1). Confirm the program is the same listing and the spending is in the same ballpark.

## Program outcome (`/pon/<pon>`)

- [ ] Open the [Improve Availability of Healthy Foods](https://fpi.omb.gov/pon/PON_455) page. Confirm the page is labeled as a program outcome, the definition describes healthier food access, and **Supplemental Nutrition Assistance Program** appears in the related programs list.
- [ ] On that PON page, open SNAP from the related programs list. Confirm it is assistance listing **10.551** and that the title matches the [SNAP listing on SAM.gov](https://sam.gov/fal/b15e4e5eabfc4ee98249fec6d0044d3c/view).

## Shared

- [ ] Review any recently changed features (see the automated tests for further guidance).
- [ ] From any page, use the header links for **Program search**, **Explore FY … spending**, and **About the FPI** (including Data, Terms & Concepts and FPI Taxonomy). Confirm each link opens the matching page and that the fiscal year in the spending link matches the year shown on the homepage.
- [ ] On the homepage, a program page, and About the FPI, compare the fiscal year used for spending. Confirm all three pages describe the same completed fiscal year.
