# UK Job Market Agents

A Python project exploring how AI agents, deterministic classification
rules, and data engineering techniques can be used to analyse the UK
data and analytics job market.

The project aims to transform job advertisements into structured,
validated datasets suitable for analysis and visualisation.

## Project Objectives

- Extract structured information from job advertisements.
- Classify roles into data engineering, data science, data analytics,
  and analytics engineering.
- Identify remote, hybrid, and onsite working arrangements.
- Extract and validate advertised salary information.
- Compare deterministic classification rules with LLM predictions.
- Identify classifications requiring further review.
- Produce reliable analytical datasets for downstream reporting.

## Architecture

The project separates responsibilities across several components:

| Component | Responsibility |
|-----------|----------------|
| Pydantic models | Validate structured job advertisement data |
| Classification rules | Apply deterministic role and working-pattern classifications |
| LLM classifier | Interpret job advertisements using a language model |
| Evaluation | Compare classification results and measure performance |
| Adjudication | Help resolve disagreements between classification methods |
| Workflow | Coordinate classification results and review decisions |
| Salary policy | Determine eligibility for annual salary analysis |
| Analytics | Construct analytical records and calculate summary metrics |
| CSV export | Serialize analytical results for downstream consumption |

## Salary Validation and Analytical Records

Salary processing separates data validation, analytical eligibility,
and classification approval.

### SalaryQuote

`SalaryQuote` is a Pydantic model that validates salary information.

It ensures that:

- At least one salary bound is provided.
- Salary bounds are positive integers.
- Minimum salaries do not exceed maximum salaries.
- The payment period is recognised: year, day, or hour.
- The currency is GBP.

A valid salary quotation is not necessarily eligible for annual
salary comparisons.

### annual_salary_bounds()

`annual_salary_bounds()` determines whether a validated salary
quotation is eligible for annual salary analysis.

Only complete annual salary ranges are eligible.

Daily rates, hourly rates, incomplete annual ranges, and missing
salary quotations return `(None, None)`.

This prevents salaries expressed in incompatible payment periods
from being compared without an explicit conversion policy.

### build_analytical_record()

`build_analytical_record()` constructs an `AnalyticalJobRecord`
from an approved classification and its associated salary quotation.

The function:

- Returns `None` when classification review is required.
- Returns `None` when no resolved classification is available.
- Retains approved advertisements without eligible annual salaries.
- Populates annual salary fields using `annual_salary_bounds()`.

For example, an approved Data Engineer advertisement offering
£500–£600 per day remains eligible for role-family and working-pattern
analysis, even though its annual salary fields are empty.

## Testing

The project uses pytest to validate model contracts, classification
behaviour, analytical policies, and workflow decisions.

Run the complete test suite:

```bash
python -m pytest -q
```

Some tests are marked as expected failures while functionality
is under development.

## Current Limitations

- The project currently relies on a small collection of example
  job advertisements.
- The end-to-end pipeline has not yet been connected to a source
  of real UK job advertisements.
- Analytical records do not currently preserve original salary
  quotations.
- A record-level export suitable for comprehensive job-market
  analysis has not yet been implemented.

## Planned Development

1. Integrate salary extraction into the LLM workflow.
2. Connect classification and salary processing into an
   end-to-end pipeline.
3. Acquire and validate real UK job advertisements.
4. Develop analysis-ready datasets with appropriate provenance.
5. Explore job-market trends using Tableau.
