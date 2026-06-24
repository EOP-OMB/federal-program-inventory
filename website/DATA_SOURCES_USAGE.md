# Data Sources Configuration

## Overview

The data sources configuration provides a centralized, single source of truth for determining which government service (Treasury.gov, USASpending.gov, or SAM.gov) is the authoritative source for program spending data.

This replaces the complex conditional logic that was previously embedded in both Python and JavaScript code.

## File Location

- **YAML Configuration**: `website/_data/data_sources.yml`
- **JavaScript Include**: `website/_includes/data-sources-config.html`
- **JavaScript Functions**: `website/_includes/scripts/_data-source-utils.html`

## 3D Lookup Structure

The configuration uses a three-dimensional lookup:

```
program_type -> year_type -> spending_type -> source
```

### Program Types
- `tax_expenditure`
- `interest`
- `contracts`
- `government_service`
- `assistance_listing`

### Year Types
- `current_year` - Spending for the current fiscal year
- `prior_year` - Spending for prior fiscal years

### Spending Types
- `obligations`
- `outlays`
- `revenue_losses`
- `expenditure`

## Usage in Liquid Templates (HTML)

### Step 1: Include the Data Sources Config

Add this include to your layout file (e.g., `_layouts/default.html`):

```liquid
{% include data-sources-config.html %}
```

This injects the configuration as a global JavaScript object: `window.DATA_SOURCES`

### Step 2a: Direct YAML Access in Liquid

For simple static lookups in HTML:

```liquid
<!-- Get the data source for assistance_listing in current year for obligations -->
<p>Data source: {{ site.data.data_sources.assistance_listing.current_year.obligations }}</p>

<!-- Output: Data source: SAM.gov -->
```

### Step 2b: Dynamic Lookup Using Variables

```liquid
{% assign program_type = page.program_type %}
{% assign year_type = 'current_year' %}
{% assign spending_type = 'obligations' %}

<p>Data source: {{ site.data.data_sources[program_type][year_type][spending_type] }}</p>
```

## Usage in JavaScript

### Step 1: Include the Data Sources Config

Same as Liquid - the include loads the config as `window.DATA_SOURCES`

### Step 2: Use the Lookup Function

#### Option A: Simple Config Lookup

```javascript
// For basic lookups when you know the current fiscal year
const source = resolveDataSourceFromConfig({
  programType: 'assistance_listing',
  dataType: 'obligations',
  year: 2024,
  currentFiscalYear: 2024
});

console.log(source); // Output: SAM.gov
```

#### Option B: Full Function (with data inference)

```javascript
// When you have a data object and want to infer the current fiscal year
const source = resolveProgramDataSource({
  programType: 'assistance_listing',
  dataType: 'obligations',
  year: 2024,
  data: obligationsData // Will call getCurrentFiscalYearFromData if currentFiscalYear not provided
});

console.log(source); // Output: SAM.gov
```

#### Option C: Using Assistance Types Instead of Program Type

```javascript
// Automatically normalize from assistance types
const source = resolveProgramDataSource({
  assistanceTypes: ['Contracts'],
  dataType: 'obligations',
  year: 2024,
  currentFiscalYear: 2024
});

console.log(source); // Output: USASpending.gov
```

#### Option D: Using CFDA

```javascript
// Automatically normalize to assistance_listing
const source = resolveProgramDataSource({
  cfda: 'SOME_CFDA_CODE',
  dataType: 'obligations',
  year: 2024,
  currentFiscalYear: 2024
});

console.log(source); // Output: SAM.gov (current year assistance listing)
```

### Example: Displaying Data Source in HTML

```html
<div class="data-source-label">
  <script>
    // Assuming programData and currentFY are defined elsewhere
    const source = resolveProgramDataSource({
      programType: programData.program_type,
      dataType: 'obligations',
      year: selectedYear,
      currentFiscalYear: currentFY,
      data: programData.obligations
    });
    
    document.write(`Data source: ${source}`);
  </script>
</div>
```

## Complete Configuration Example

Here's how the configuration handles a specific case:

```yaml
assistance_listing:
  current_year:
    obligations: SAM.gov
    outlays: USASpending.gov
    revenue_losses: USASpending.gov
    expenditure: SAM.gov
  prior_year:
    obligations: USASpending.gov
    outlays: USASpending.gov
    revenue_losses: USASpending.gov
    expenditure: USASpending.gov
```

This means:
- For assistance listings in the current fiscal year: use SAM.gov for obligations and expenditure, USASpending.gov for outlays/revenue_losses
- For assistance listings in prior years: always use USASpending.gov

## Migration from Old Conditional Logic

### Before (Complex Conditionals)

```javascript
// Old approach - embedded logic in JavaScript
if (programType === 'tax_expenditure') {
  return 'Treasury.gov';
}
if (dataType === 'obligations') {
  if (programType === 'assistance_listing') {
    return year === currentFiscalYear ? 'SAM.gov' : 'USASpending.gov';
  }
}
// ... more conditions
```

### After (Simple Lookup)

```javascript
// New approach - configuration-driven
const source = resolveDataSourceFromConfig({
  programType: 'tax_expenditure',
  dataType: 'obligations',
  year: 2024,
  currentFiscalYear: 2024
});

console.log(source); // Treasury.gov
```

## Adding New Spending Types or Sources

If you need to add a new spending type or modify the source mappings:

1. Edit `website/_data/data_sources.yml`
2. Add the new spending type under the appropriate program type and year combinations
3. No changes needed to Python or JavaScript code - they automatically use the updated configuration

## Benefits

1. **DRY (Don't Repeat Yourself)** - Single source of truth instead of duplicated logic
2. **Maintainability** - Changes in one place cascade to all code
3. **Clarity** - Configuration is explicit and easy to understand
4. **Consistency** - HTML and JavaScript use the same data
5. **Testability** - Configuration can be validated independently
6. **Performance** - No complex conditional evaluation needed at runtime
