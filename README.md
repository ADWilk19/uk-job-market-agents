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
| Adzuna API client | Retrieve provider data with bounded pagination, validation/error handling and injectable transport |
| Ingestion pipeline | Fetch, adapt and deduplicate advertisements by `(source, source_id)` |
| Source adapters | Translate provider-specific advertisements into validated JobPosting objects |
| Classification rules | Apply deterministic role and working-pattern classifications |
| LLM classifier | Interpret job advertisements using a language model |
| LLM salary extractor | Extract structured salary quotations and supporting evidence |
| Salary verification | Check extracted values against evidence and assign review status |
| Evaluation | Compare classification results and measure performance |
| Adjudication | Help resolve disagreements between classification methods |
| Workflow | Coordinate classification results and review decisions |
| Orchestration | Coordinate single-job classification, salary verification and analytical record construction |
| Batch orchestration | Process advertisements sequentially, preserve outcomes and isolate failures |
| Batch metrics | Calculate validated processing counts and derived rates |
| Salary policy | Determine eligibility for annual salary analysis |
| Analytics | Construct analytical records and calculate summary metrics |
| CSV export | Serialize analytical results for downstream consumption |
| Batch reporting | Serialize validated batch metrics into deterministic CSV output |

## Job Advertisement Ingestion Contract

`JobPosting` provides the canonical internal representation of a job advertisement, independently of the external data provider.

Incoming advertisements must satisfy the following requirements:

- `source` and `source_id` must contain non-whitespace characters.
- `collected_at` must be a timezone-aware datetime.
- `raw_title` and `raw_description` must contain non-whitespace characters.
- `source_url` is optional but must be a valid HTTP/HTTPS URL when supplied.
- `company_name` and `location_raw` remain optional.

Validation rejects blank source fields and advertisement content without stripping or otherwise modifying valid raw strings.

Newly collected advertisements can retain their default `UNKNOWN` classifications and `UNVALIDATED` status until the processing workflows evaluate them.

The model preserves source identity and collection timestamps to support provenance and deduplication.

The Adzuna source adapter, `adapt_adzuna_job()`, translates provider-specific advertisement data into validated `JobPosting` objects. It preserves source identifiers, URLs, raw titles, descriptions, company names and locations where supplied.

`DescriptionCompleteness` distinguishes `COMPLETE`, `EXCERPT` and `UNKNOWN` advertisement descriptions. The Adzuna adapter conservatively marks descriptions as `EXCERPT`; other `JobPosting` instances default to `UNKNOWN`.

`process_job()` preserves source identity, collection timestamps, source URLs and description completeness in `OrchestrationResult`, whether classification succeeds or requires review.

The Adzuna retrieval client and ingestion pipeline support controlled live retrieval and offline snapshot replay (Lesson 21). Persistent ingestion history and a comprehensive provenance-aware analytical export remain future work.

### Lesson 20 — Adzuna API client and ingestion pipeline

- Implemented the Adzuna API client with bounded pagination and validation/error handling.
- Kept HTTP transport injectable so API behaviour can be tested with mocked transport and deterministic responses.
- Implemented `deduplicate_postings()` using `(source, source_id)`, preserving the first occurrence and first-seen order.
- Implemented `prepare_adzuna_postings()` to adapt raw advertisements into validated `JobPosting` objects and deduplicate them.
- Implemented `ingest_adzuna_jobs()` to coordinate fetching, preparation and deduplication, with injectable `fetch_pages` and transport dependencies.
- Passed the timezone-aware collection timestamp through the pipeline using the keyword-only `collected_at` argument.
- Verified the Lesson 20 pipeline with mocked transport/dependencies; live smoke support follows in Lesson 21.

Adzuna credentials must remain local and must not be committed, including in fixtures, documentation or request logs. Use the existing ignored secrets configuration and verify that credentials are excluded before committing.

**Compatibility:** Introducing timezone-aware collection timestamps required updating existing test fixtures. The full regression suite passed with 190 tests and one expected failure on 22 October 2026.

### Lesson 21 — Controlled Adzuna smoke and snapshot replay

From the repository root, with project dependencies installed in `.venv`:

```bash
# Default: replay the existing local snapshot; no credentials or HTTP calls.
.venv/bin/python -m scripts.smoke_adzuna
# Replay a different snapshot.
.venv/bin/python -m scripts.smoke_adzuna --snapshot data/raw/another_sample.json
# Fetch one UK page for "data engineer", requesting five results, and save it.
.venv/bin/python -m scripts.smoke_adzuna --live
# Choose the destination for a fresh response.
.venv/bin/python -m scripts.smoke_adzuna --live --snapshot data/raw/another_sample.json
```

Live mode requires `ADZUNA_APP_ID` and `ADZUNA_APP_KEY` in the environment;
the script does not load `secrets.json` automatically. Keep values in local
secret storage and inject them into the environment without recording them
in shell history. Never commit credentials or log the constructed request URL:
it contains credentials. The smoke script suppresses request exception details,
reporting only an HTTP status or a generic request failure.

The default snapshot is `data/raw/adzuna_sample.json`. Both `data/raw/` and
`secrets.json` are ignored and must remain untracked. A fresh checkout has no
snapshot: obtain one locally before replay. Custom paths outside `data/raw/`
are not covered by that ignore rule and must also stay out of commits.

Both modes adapt and deduplicate the response and print retrieved/validated
counts. The existing local snapshot replay produced **5 retrieved / 5 unique
validated postings** on 27 October 2026; no fresh live request was made during
this close-out.

The adapter now preserves publication time, paired coordinates, raw contract
and category metadata, and provider salary bounds/prediction status. Coordinates
must be in range and supplied together; publication times must be timezone-aware.
Provider salary bounds are non-negative and ordered, and remain separate from
interpreted salary fields. Prediction flags accept only `"0"`, `"1"` or `None`;
empty optional contract/category text becomes `None`.

**Testing:** `tests/test_smoke_adzuna.py` creates a synthetic temporary snapshot,
removes both credentials and replaces HTTP transport with a function that fails
if called. This guards the offline default without depending on a live API or
committed provider data. Run focused tests before the full suite:

```bash
.venv/bin/python -m pytest -q tests/test_smoke_adzuna.py tests/ingestion tests/test_job_posting.py
.venv/bin/python -m pytest -q -ra
```

**Caveats:** `--live` overwrites the chosen snapshot before adapting its adverts.
Replay assigns the current UTC time to `collected_at`, not the original fetch
time; the snapshot does not store that timestamp. Malformed JSON or an invalid
advert can stop the smoke run. Descriptions remain excerpts and predicted
salaries are provider metadata, not verified advertised salaries. This small
sample validates ingestion, not market coverage or end-to-end LLM processing.

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

## Batch Operational Metrics

`BatchSummary` provides deterministic aggregate statistics derived
from validated `BatchProcessingOutcome` objects.

The `summarize_batch()` function calculates:

- Total advertisements processed in the batch.
- Advertisements successfully processed.
- Advertisements requiring classification review.
- Advertisements that failed during processing.

`BatchSummary` also exposes three calculated proportions:

- `processed_rate`
- `review_rate`
- `failure_rate`

Rates range from 0.0 to 1.0. Empty batches return zero counts and
zero rates, avoiding division-by-zero errors.

Pydantic validation enforces non-negative counts and requires the
individual status counts to sum to the batch total.

Batch aggregation is deterministic and does not invoke an LLM.

The calculated rates are Python properties and are not currently
included in Pydantic's standard `model_dump()` output.

### Batch Metrics CSV Export

`write_batch_summary_csv()` serializes a validated `BatchSummary`
into a deterministic, single-row CSV report.

The export uses this fixed column order:

```csv
total,processed,review_required,failed,processed_rate,review_rate,failure_rate
```

Processing, review and failure rates are represented as proportions
between 0 and 1, formatted to six decimal places.
The exporter guarantees:

- A stable seven-column schema.
- Exactly one data row per summary.
- LF (`\n`) line endings and a final newline.
- Zero counts and zero rates for empty batches.
- Identical output for identical input summaries.

Serialization is separate from aggregation and does not invoke an LLM.
The exporter accepts a writable text stream, allowing output to
in-memory buffers or files.

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

**Verified full-suite result:** **240 passed, 2 skipped, 1 xfailed**
(27 October 2026). The two OpenAI integration tests skip without
`OPENAI_API_KEY`; the expected failure is the known remote-first versus
mandatory office-attendance rule case. Focused smoke, ingestion and
`JobPosting` tests: **74 passed**.

Lesson 20 is integrated into local `main` at `a3068b1`. Lesson 21 is
completed on `lesson/21-adzuna-live-smoke`, without merging into `main`.

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

1. Connect validated real postings to the processing workflow with explicit excerpt and salary policies.
2. Develop analysis-ready datasets with appropriate provenance.
3. Build operational monitoring and job-market dashboards.
4. Investigate processing retries, persistence and concurrency where justified.
