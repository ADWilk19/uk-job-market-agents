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
| --------- | -------------- |
| Pydantic models | Validate structured job advertisement data |
| Classification rules | Apply deterministic role and working-pattern classifications |
| LLM classifier | Interpret job advertisements using a language model |
| LLM salary extractor | Extract structured salary quotations and supporting evidence |
| Salary verification | Check extracted values against evidence and assign review status |
| Evaluation | Compare classification results and measure performance |
| Adjudication | Help resolve disagreements between classification methods |
| Workflow | Coordinate classification results and review decisions |
| Orchestration | Coordinate single-job classification, salary verification and analytical record construction |
| Batch orchestration | Process advertisements sequentially, preserve outcomes and isolate failures |
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

- Accepts optional `company_name` and `location_raw` parameters,
  preserving the advertised employer and location. `process_job()`
  supplies these fields from the `JobPosting`.
- Returns `None` when classification review is required.
- Returns `None` when no resolved classification is available.
- Retains approved advertisements without eligible annual salaries.
- Populates annual salary fields using `annual_salary_bounds()`.

For example, an approved Data Engineer advertisement offering
£500–£600 per day remains eligible for role-family and working-pattern
analysis, even though its annual salary fields are empty.

## Salary extraction and analytical eligibility

The system uses structured LLM output to identify salary information and supporting evidence.
Deterministic verification assigns a review status before the extracted salary is considered for analytics.
All salary assessments can be exported to an auditable CSV, including those requiring review or containing no disclosed salary.
Only verified GBP annual salary ranges with both bounds present are eligible for annual salary statistics.
Daily and hourly rates are not annualised. Ineligible salaries are excluded from salary calculations without
removing their associated advertisements from job counts.

The single-job orchestrator `process_job()` applies the salary integration
adapter after salary extraction and verification. This path is covered by
orchestration tests; real-world ingestion is not yet connected.

## Orchestration

`process_job(job: JobPosting) -> OrchestrationResult` coordinates the
single-job classification and salary workflows.

The orchestrator:

- Classifies the raw title and description, then resolves the classification.
- Builds an analytical record, preserving `company_name` and `location_raw`.
- Stops before salary extraction if classification review is required or no
  resolved classification is available.
- For an approved advertisement, extracts and verifies salary information
  from the raw description, then applies the salary assessment to the record.
- Retains the approved advertisement when salary review is required, salary
  is not disclosed, or the quotation is ineligible for annual analysis.
  Annual salary fields remain empty in these cases.

`OrchestrationResult` contains `classification` (`WorkflowResolution`),
`analytical_record` (`AnalyticalJobRecord` or `None`) and
`salary_assessment` (`SalaryAssessment` or `None`). When classification
prevents record construction, both optional fields are `None`.

Only verified, complete GBP annual salary ranges populate annual salary
fields. Classification review and salary review therefore have distinct
consequences: the former prevents an analytical record; the latter does
not remove an otherwise approved advertisement from job counts.

The single-job orchestrator is reused by the batch-processing workflow
described below.

## Batch Orchestration

The batch orchestration workflow processes multiple job advertisements
sequentially using the existing `process_job()` function.

`process_jobs()` returns a list of `BatchProcessingOutcome` objects,
preserving advertisement identifiers and input order.

Each outcome has one of three statuses:

- `PROCESSED`: Classification completed without requiring review.
- `REVIEW_REQUIRED`: Classification completed but requires review.
- `FAILED`: Processing raised an exception.

Pydantic model validators enforce consistency between processing status,
classification decisions, orchestration results, and error messages.

Individual processing failures are isolated so subsequent advertisements
can continue processing.

The current implementation is sequential and does not support
concurrency, retries, or persistent processing history.

## CSV Export Contract

`write_salary_analysis_csv` accepts a sequence of `SalaryAnalysisRow`
instances and writes aggregated salary-analysis results to a CSV file.

The exporter guarantees:

- **Column schema:** The following six columns are written in the specified order:

  ```csv
  dimension,segment,records,records_with_salary,average_midpoint,has_sufficient_sample
  ```

- **Deterministic output:** Identical input rows, supplied in the same order,
  produce identical CSV bytes. The exporter does not automatically sort rows.
- **Line endings:** The exporter uses LF (`\n`) line endings, regardless of
  operating system.
- **Missing values:** An unavailable `average_midpoint` is represented by
  an empty CSV field.

The export contains aggregated salary-analysis summaries rather than
individual job advertisements.

### Salary extraction CSV

`write_salary_extraction_csv()` exports individual salary assessments,
including verified, review-required, and not-disclosed results.

The export contains eight columns:

```csv
job_id,salary_min,salary_max,period,currency,evidence,review_status,review_reason
```

The exporter preserves input order, uses LF line endings, and represents
missing values as empty fields. Identical ordered inputs produce identical
CSV bytes.

This record-level audit export is separate from the aggregated salary
analysis CSV.

## Testing

The project uses pytest to validate model contracts, classification
behaviour, analytical policies, and workflow decisions.

Run the complete test suite:

```bash
python -m pytest -q
```

The latest confirmed full-suite result is **158 passed, 1 xfailed**
(19 October 2026), following implementation of Lesson 15.

The Lesson 15 implementation is on `lesson/15-batch-orchestration`.
It has not yet been merged into `main`.

The tested baseline is `main` at commit `6dc5650`, fast-forwarded from
Lesson 14 and pushed to `origin/main`.

## Current Limitations

- Batch processing is sequential, without concurrency, retries or
  persistent processing history.
- The project currently relies on a small collection of example
  job advertisements.
- The end-to-end pipeline has not yet been connected to a source
  of real UK job advertisements.
- Analytical records do not currently preserve original salary
  quotations.
- A comprehensive record-level export combining job classifications, salary assessments, and provenance has not yet been implemented.

## Planned Development

1. Develop batch-level operational metrics and structured processing reports.
2. Acquire and validate real UK job advertisements.
3. Develop analysis-ready datasets with appropriate provenance.
4. Explore job-market trends using interactive dashboards.
5. Investigate processing retries, persistence and concurrency where justified.
6. Acquire and validate real UK job advertisements.
7. Develop analysis-ready datasets with appropriate provenance.
8. Explore job-market trends using locally hosted Python visualisations and interactive dashboards.
