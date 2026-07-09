---
name: excel-forest-plot
description: Create Excel-ready forest plot workbooks and step-by-step Excel instructions from HR, OR, RR, risk ratio, hazard ratio, odds ratio, and 95% CI data. Use when the user asks to make a forest plot or 森林图 in Excel, needs vertical forest plot data layout, custom error bars, an HR=1 reference line, or an .xlsx template for point estimates with confidence intervals.
---

# Excel Forest Plot

## Overview

Help the user turn point estimates and confidence intervals into an Excel forest plot. Default to a vertical Excel chart because it is easiest to maintain with native Excel category axes and custom vertical error bars.

## Workflow

1. Extract one row per comparison:
   - `label`
   - `estimate` such as HR, OR, or RR
   - `lower` confidence limit
   - `upper` confidence limit

2. Validate the values before plotting:
   - Require `lower <= estimate <= upper`.
   - Require positive values if using a log-scale axis.
   - Preserve the user's original labels when provided; otherwise use `Group 1`, `Group 2`, etc.

3. Add Excel helper columns:
   - `Minus error = Estimate - Lower CI`
   - `Plus error = Upper CI - Estimate`
   - `Reference = 1`

4. For an `.xlsx` deliverable, run `scripts/create_forest_plot_workbook.py`.

5. For instructions-only answers, give the user the completed data table plus concise Excel steps for adding custom error bars and the reference line.

## Script Usage

Use the bundled script when the user wants a file, template, or repeatable output:

```bash
cd <excel-forest-plot-skill-directory>
python3 scripts/create_forest_plot_workbook.py \
  --output forest_plot.xlsx \
  --data "Group 1,0.80,0.66,0.97;Group 2,0.76,0.64,0.91"
```

CSV input is also supported:

```bash
cd <excel-forest-plot-skill-directory>
python3 scripts/create_forest_plot_workbook.py \
  --input-csv input.csv \
  --output forest_plot.xlsx
```

Accepted CSV column names:

- Label: `label`, `group`, `name`, or `study`
- Estimate: `estimate`, `hr`, `or`, `rr`, or `value`
- Lower CI: `lower`, `low`, `lcl`, or `ci_low`
- Upper CI: `upper`, `high`, `ucl`, or `ci_high`

## Manual Excel Steps

Use this structure when explaining how to create the chart in Excel:

1. Enter columns: `Group`, `Estimate`, `Lower CI`, `Upper CI`, `Minus error`, `Plus error`, `Reference`.
2. Calculate `Minus error` as `=Estimate - Lower CI`.
3. Calculate `Plus error` as `=Upper CI - Estimate`.
4. Insert a line chart with markers using `Group` as categories and `Estimate` as values.
5. Remove the estimate line so only markers remain.
6. Add vertical error bars, choose custom values, set positive values to `Plus error`, and negative values to `Minus error`.
7. Add `Reference` as a second series, format it as a dashed line, and remove its markers.
8. Format the value axis:
   - Use log scale for HR, OR, or RR when all values are positive.
   - Set a sensible minimum and maximum that include every CI and `1`.
   - Add a clear axis title such as `Hazard ratio (log scale)`.

## Output Standards

- Show the exact Excel-ready table when answering in chat.
- State that Excel does not have a native forest plot chart type; the practical method is a line or scatter chart plus custom error bars.
- Keep the reference line at `1` for ratio measures unless the user specifies another null value.
- Do not use bars for HR/OR/RR confidence intervals.
- Mention when a CI crosses `1`; otherwise avoid over-interpreting clinical meaning without group definitions.
