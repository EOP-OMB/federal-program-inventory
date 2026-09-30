# E2E tests

Automated tests run in the `cypress` container.

## Home

- [ ] Homepage fixture loads
- [ ] Spending tooltip opens and closes on desktop
- [ ] Spending tooltip opens and closes on tablet
- [ ] Spending tooltip closes via icon, close button, and outside click
- [ ] Spending tooltip opens and closes on iPhone 8
- [ ] Header displays
- [ ] Header navigation visual regression (desktop)
- [ ] Header navigation visual regression (narrow viewport, expanded)
- [ ] Footer displays
- [ ] Footer banner displays
- [ ] Footer links display
- [ ] Footer banner visual regression
- [ ] Footer visual regression
- [ ] Return-to-top link appears after scrolling to the bottom

## Search

- [ ] Applicant filter wrapping at a wide viewport
- [ ] Search within PON filter
- [ ] Program name sorting
- [ ] Keyword search defaults to relevancy sorting
- [ ] Agency, GWO, and PON filters serialize and restore from the URL
- [ ] Search text and result count restore after refresh
- [ ] Clear filters restores search text, applicant filters, and global count
- [ ] Loading-results skeleton screenshot
- [ ] Full search page snapshot in mobile view
- [ ] Empty results hide the program list and pagination
- [ ] API error shows the retry message
- [ ] Pagination requests the next page and renders its programs
- [ ] Agency select-all checks sub-agencies and encodes them in the URL
- [ ] Category and assistance filters serialize and restore from the URL
- [ ] An exact CFDA match redirects to the program permalink
- [ ] Obligations tooltip shows a data source label

## Program

- [ ] Populated overview, results, authorization, and oversight content
- [ ] Empty program hides purpose, results, and authorization content
- [ ] Objective without outcomes or results shows fallback copy
- [ ] Arrow keys move between program tabs
- [ ] Full-page tab screenshots (overview, spending, results, authorization, oversight)
- [ ] Responsive tab screenshots
- [ ] Full-page snapshot in mobile view
- [ ] Authorization tab: rules and authorizations show
- [ ] Authorization tab: rules only
- [ ] Authorization tab: authorizations only
- [ ] Authorization tab: neither rules nor authorizations
- [ ] Authorization tab visual regression
- [ ] Overview chart: obligations less than outlays, outlays null
- [ ] Overview chart: missing data series
- [ ] Overview chart: no data
- [ ] Overview chart: one year
- [ ] Overview chart: one year stacked
- [ ] Overview chart: other program spending
- [ ] Overview chart: legend and coinciding series
- [ ] Overview chart tooltip
- [ ] Overview chart tooltip shows a data source label
- [ ] Spending chart: small bar
- [ ] Spending chart: negative obligation
- [ ] Spending chart: negative outlay
- [ ] Spending chart: no baseline (toggle hidden)
- [ ] Spending chart: outlay label covered
- [ ] Spending chart: unreported years treated as zero
- [ ] Spending chart: no data
- [ ] Spending chart: negative padding
- [ ] Spending chart: other program spending
- [ ] Spending chart tooltip
- [ ] Spending chart dollar amount formatting
- [ ] Spending chart tooltip shows a data source label
- [ ] Improper payment card at 0% rate (section, layout, percentage, amount, FY label)
- [ ] Improper payment card at a positive rate (section, layout, percentage, amount, FY label)
- [ ] Improper payment card grayed out with N/A when data is missing
- [ ] Improper payment card shows Multiple / Varies when `improper_payments_is_multiple` is true
- [ ] Improper payments section: one FPI program, one IP program with values
- [ ] Improper payments section: multiple FPI programs, one IP program with values
- [ ] Improper payments section: one FPI program, one IP program without values
- [ ] Improper payments section: multiple FPI programs, one IP program without values
- [ ] Improper payments section: one FPI program, multiple IP programs with values
- [ ] Improper payments section: multiple FPI programs, multiple IP programs with values
- [ ] Improper payments section: one FPI program, multiple IP programs without values
- [ ] Improper payments section: multiple FPI programs, multiple IP programs without values
- [ ] Improper payments section: no mappings
- [ ] USAID program page shows the USAID alert
- [ ] Breadcrumbs with a sub-agency
- [ ] Breadcrumbs without a sub-agency show agency and program only
- [ ] Category list section with one item, and Housing filter on search
- [ ] Applicant list section with multiple items
- [ ] Program type list section with one item, and assistance filter on search
- [ ] List section with no items
- [ ] Beneficiaries list shows list items and no filter chips
- [ ] Category and subcategory tags on the program page
- [ ] Visited program links use the visited color

## Government-wide objective (GWO)

- [ ] Full page screenshot
- [ ] Full page screenshot on phone
- [ ] Treemap tile for each nonzero program
- [ ] Treemap program labels, percentages, and wrapping
- [ ] Treemap tooltip with name, amount, and percentage
- [ ] Clicking a treemap tile navigates to the program
- [ ] Jump link to the related programs table
- [ ] Treemap and related table tooltips show data source labels
- [ ] Default description when the GWO description is blank
- [ ] Default description when the GWO description is missing
- [ ] Insight copy for 0 programs
- [ ] Insight copy for 1 program
- [ ] Insight copy for many programs
- [ ] Insight copy for many programs totaling $0
- [ ] Info card shows Programs, FY title, and Agencies
- [ ] Info card does not contain "Expended so far this year"
- [ ] Info card snapshot and structure
- [ ] Target count card shows the GWO program count
- [ ] Category and subcategory tags on the GWO page

## Program outcome (PON)

- [ ] Full page screenshot
- [ ] Full page screenshot on phone
- [ ] Treemap tile for each nonzero program
- [ ] Treemap program labels and percentages
- [ ] Treemap tooltip with name, amount, and percentage
- [ ] Clicking a treemap tile navigates to the program
- [ ] Jump link to the related programs table
- [ ] Treemap and related table tooltips show data source labels
- [ ] Info card shows Programs, FY title, and Agencies
- [ ] Info card does not contain "Expended so far this year"
- [ ] Info card structure
- [ ] Target count card shows the PON program count
- [ ] Category and subcategory tags on the PON page

## Category and subcategory

- [ ] Category index full page screenshot
- [ ] Category index full page screenshot on phone
- [ ] Category page full page screenshot
- [ ] Category page full page screenshot on phone (including agency and applicant views)
- [ ] Subcategory page full page screenshot
- [ ] Subcategory page full page screenshot on phone (including agency and applicant views)
- [ ] Empty subcategory shows empty-state copy and hides the chart
- [ ] Empty subcategory shows empty-state copy and hides tables
- [ ] Subcategory view-by radios show the matching table
- [ ] Subcategory pagination and title sort stay on the fixture page
- [ ] Category view-by radios show the matching table
- [ ] Category dropdown enables subcategories without leaving the fixture

## About

- [ ] About terms full page screenshot
- [ ] About terms nav responsiveness
- [ ] About FPI full page screenshot
- [ ] About download table files download successfully
- [ ] Taxonomy full page snapshot
- [ ] Taxonomy full page snapshot on mobile
- [ ] Taxonomy default load shows the first page in ascending order
- [ ] Taxonomy sorting toggles descending order without changing the result count
- [ ] Taxonomy pagination advances to the remaining rows
- [ ] Taxonomy category filter keeps only mapped objectives
- [ ] Taxonomy unmapped category shows the empty-filter state
- [ ] Taxonomy clear filters restores the full sorted table
- [ ] Taxonomy keyword search hides non-matching category options

## Shared and accessibility

- [ ] Tooltip opens, contains a link, and closes on Escape
- [ ] External link uses the accessible new-tab pattern
- [ ] Sortable table defaults to amount descending and keeps the total last
- [ ] No page contains "Expended so far this year"
- [ ] 508 scan of core pages (`/`, `/search`, `/about/fpi`, `/about/terms`, `/about/taxonomy`, `/category`)
- [ ] 508 scan of Cypress fixture pages
- [ ] 508 scan of program tabs
- [ ] 508 scan of search with expanded filters
- [ ] 508 scan of mobile nav with About submenu expanded
- [ ] 508 scan of taxonomy filters, sort, and pagination
- [ ] 508 scan of subcategory table mode radios
- [ ] 508 scan of homepage spending tooltip open state
