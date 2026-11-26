# From Job Advertisements to Trustworthy Analytics

*An agent-assisted data pipeline for evaluating UK job advertisements sourced from Adzuna.*

**Status:** Working manuscript — Lesson 44 local empirical replay reviewed; publication requirements remain open
**Target publication:** 15 December 2026

## 1. Introduction

Job advertisement data presents several analytical challenges, including repeated content, ambiguous role descriptions, estimated salaries and inconsistent salary formats.

This project investigates how agent-assisted interpretation and deterministic validation can transform such data into trustworthy, reproducible analytical outputs.

The objective is to demonstrate a reliable analytical methodology rather than estimate the characteristics of the UK labour market as a whole.

## 2. Data provenance

The exploratory analysis uses three saved Adzuna UK API responses collected on 16 November 2026.

| Search query | Returned advertisements |
| --- | ---: |
| Data engineer | 20 |
| Analytics engineer | 20 |
| Data scientist | 20 |
| Total | 60 |

Each response contains the first page of search results. The combined sample is neither random nor representative of the wider UK labour market.

Search queries are not equivalent to validated occupational classifications.

## 3. System architecture

The pipeline separates probabilistic interpretation from deterministic enforcement.

LLM agents interpret ambiguous advertisement content, propose classifications and extract candidate salary evidence.

Python and Pydantic enforce structural validity, evidence provenance, numerical constraints, supported salary periods, analytical eligibility and output serialization.

An agent's interpretation does not automatically become an accepted analytical observation.

## 4. Finding: Advertisement identity is not vacancy identity

The combined sample contains 60 distinct Adzuna advertisement IDs, with no ID overlap between the three sampled search-result pages.

However, only 47 distinct advertiser/title/description-excerpt combinations were identified. Eighteen advertisements belonged to five repeated-content groups.

Unique provider identifiers therefore do not guarantee unique advertisement content.

Repeated content is treated as a data-quality diagnostic rather than definitive evidence of duplicate vacancies. All 60 advertisements remain in the exploratory denominator; the 47 content combinations are not a deduplicated vacancy population.

## 5. Finding: Data completeness does not establish reliability

Of the 60 sampled advertisements, 42 (70%) contained salary metadata flagged by Adzuna as predicted.

Only 12 of the 60 description excerpts (20%) contained a sterling symbol. Both percentages use all 60 advertisements, including repeated content, as their denominator.

Neither provider salary metadata nor the presence of a currency symbol independently establishes a verified annual salary.

Two deliberately selected comparisons also identified provider-predicted salary maxima exceeding the visible advertised upper bounds by 13.1% and 25.7%.

These comparisons demonstrate the existence of discrepancies, not their prevalence. The annual periods in these two comparisons were inferred from role/context, not explicitly stated in the quoted ranges; the manual values are not production-verified annual salaries.

## 6. Finding: Recognition does not establish analytical eligibility

A separate controlled benchmark uses eight manually selected salary quotations from the 20-advertisement data-engineering snapshot, one quotation per pound-bearing excerpt. These eight quotations are a subset of the 60-advertisement exploration, not an additional population. Every fraction in the following table has the same eight-quotation denominator; synthetic controls are excluded.

| Evaluation stage | Quotations |
| --- | ---: |
| Pre-Lesson 37 range parser (`f2f2f86`) | 0/8 |
| Post-Lesson 37 range parser (`5f37e1f`) | 0/8 |
| Historical Lesson 39 range parser (`596b74c`) | 0/8 |
| Legacy range parser following Lesson 40 (`6134888`) | 1/8 |
| Expanded salary evidence recognition | 8/8 |
| Deterministically verified quotations | 3/8 |
| Eligible under annual salary policy in the controlled replay | 1/8 |
| Without a supported stated period | 5/8 |

Notebook 02 freezes the pre/post-Lesson 37 comparison at 0/8 versus 0/8. Lesson 40 subsequently added `pa` to the legacy range helper and introduced the expanded evidence recogniser; these are separate historical comparisons. The expanded recogniser improved format coverage on this selected fixture without relaxing analytical eligibility requirements.

Daily rates, approximate amounts and quotations without explicit supported salary periods cannot automatically enter annual salary analysis.

The three verified quotations comprise two daily rates (`observed_00` and `observed_01`) and one annual range (`observed_17`, £76,000–£95,000 pa). The other five require review; `observed_16` is also approximate.

This benchmark evaluates deterministic recognition and verification using constructed extraction candidates. It does not independently measure LLM extraction accuracy. The replay bypasses the production description-completeness gate for diagnostic purposes. The 1/8 salary-policy pass does not establish that an excerpt would enter a production report, or that one of the full 60 advertisements is the final report population.

Notebook 01 asks a narrower diagnostic question across the three snapshots: using the current package, the first strict range match in each of 12 pound-bearing excerpts yields two verified quotations and one annual-policy pass. Its original Lesson 36 result was one verified daily range and zero annual-policy passes. Neither diagnostic measures automatic evidence extraction, and the 2/12 strict-match count must not be substituted for the expanded recogniser's 8/8 selected-quotation result.

### Synthetic integration evidence — Lesson 43

A separate [six-advertisement integration test](../tests/analytics/test_end_to_end_reconciliation.py)
checks the production path from classification rules and resolution through
orchestration, salary verification, record-level row construction and analytical
report CSVs. Only the classifier and salary extractor's LLM-facing functions use
controlled responses. This tests deterministic handling of those responses, not
measured LLM accuracy or empirical market characteristics.

| Synthetic scenario | Processing result | Salary result |
| --- | --- | --- |
| Explicit annual range | Processed | Verified and annual eligible |
| Explicit daily range | Processed | Verified, excluded from annual analytics |
| No stated period; candidate asserts annual | Processed | Salary review required; role retained |
| Excerpt with pay text and predicted provider bounds | Processed | Extraction gated off; provider metadata retained separately |
| Classification disagreement | Classification review required | No extraction or analytical role |
| Classification-agent failure | Failed | No extraction or analytical role |

All six advertisements remain in the source/export-row population: four process,
one requires classification review and one fails. Salary extraction is attempted
for three, and two assessments verify. Report CSVs reconcile role eligibility at
**4/6** and annual salary eligibility at **1/6**. The within-role annual salary rate
is **1/4**, using four eligible data-engineering records as its denominator.
Classification review and salary review remain separate decisions.

These six synthetic inputs are neither part of the 60-advertisement Adzuna sample
nor the eight-quotation benchmark. The completeness gate is preserved rather
than bypassed: an excerpt's explicit salary text and provider estimate do not
populate verified analytical salary fields. Record-level row construction is
exercised, but record-level CSV serialization is not part of this integration test.
The synthetic test can run without private snapshots or API credentials once
dependencies are installed. It does not by itself establish the empirical replay
reported below or public reproducibility of the Adzuna findings.

### Snapshot-backed empirical classification replay — Lesson 44

[Notebook 03](../notebooks/03_empirical_classification_replay.ipynb) now runs the
original 60 observations through production classification reconciliation,
orchestration, record-level export and analytical reporting using locally captured
LLM responses. This extends the synthetic integration evidence above without
reclassifying it as market data or treating the eight selected salary quotations
as the full analytical population.

| Measurement | Numerator / denominator | Rate |
| --- | --- | --- |
| Role-family agreement | 59/60 | 98.33% |
| Work-pattern agreement | 51/60 | 85.00% |
| Work-pattern agreement excluding mutual unknowns | 16/25 | 64.00% |
| Approved role coverage | 50/60 | 83.33% |
| Approved known work-pattern coverage | 16/60 | 26.67% |
| Verified annual salary coverage | 0/60 | 0% |

Rules and captured interpretations agree on 16 hybrid and 35 unknown work patterns.
All three rules-based onsite classifications disagree with captured hybrid labels;
six rules-based unknowns receive specific captured labels (two each hybrid, onsite
and remote). At least one hybrid rationale assumes office expectations absent
from the saved excerpt. These findings expose limitations in both approaches;
agreement is not independently validated accuracy.

Processing yields 50 approved, 10 requiring classification review (nine work-pattern,
one role-family) and no failures. The approved population contains:

| Role | Hybrid | Unknown | Total |
| --- | ---: | ---: | ---: |
| Analytics engineering | 3 | 16 | 19 |
| Data engineering | 4 | 10 | 14 |
| Data science | 9 | 8 | 17 |
| Total | 16 | 34 | 50 |

All denominators for overall coverage remain 60, including the ten review records.
All descriptions are excerpts: production salary extraction is gated off, so no
verified annual salary enters these reports. Provider estimates remain separate.
This zero is a policy result, not a salary-disclosure estimate, and does not
contradict Lesson 41's one annual-eligible quotation in a diagnostic bypass.

Local publication covers record-level jobs, batch summary, analytical samples and
role-family summary CSVs (7,931, 117, 107 and 145 bytes respectively). Repeated
execution produces matching SHA-256 fingerprints for all four, with source IDs,
status counts and analytical denominators reconciled. The new empirical path
includes record-level CSV serialization, unlike the Lesson 43 test.

## 7. Reproducibility

The project uses saved API responses, labelled evidence fixtures, version-controlled implementations and automated regression tests.

Notebook 02 loads the original range-parser definitions from the full commit IDs corresponding to `f2f2f86` and `5f37e1f`, independently of the working production package. Both Git objects must be available locally. The Lesson 39/40 historical results above are separately attributed to their commits.

The exploratory notebooks and controlled salary replay can be executed without live API or LLM credentials when the required local inputs are available.

Raw responses in `data/raw/` are excluded from Git. A public checkout alone cannot reproduce these snapshot-based results. Missing snapshots cause notebook loading to fail; snapshot-dependent tests skip rather than retrieve new data, and a skip is not a reproduced measurement. Dependencies and the required Git history must also be available. See the [notebook setup instructions](../README.md#reproduce-the-notebook-offline) and [Lesson 41 replay procedure](../README.md#lesson-41--controlled-offline-salary-verification-replay).

**Outstanding publication considerations:** confirm applicable Adzuna data-redistribution permissions and attribution requirements before publishing source data or excerpts; establish and document a compliant way for readers to access the required evidence and reproduce the workflow. This review does not establish redistribution clearance or complete public reproducibility. Local snapshot-backed empirical classification, report counts, exclusions and denominators now reconcile in Lesson 44; compliant public access and reader reproduction remain outstanding under the [release Definition of Done](../COURSE_PROGRESS.md#definition-of-done--first-portfolio-release).

Lesson 44 requires the three snapshots and their metadata sidecars plus the local
`classification_lesson44.jsonl` capture file. Replay validates identities, exact
input/prompt fingerprints and model identifiers and returns isolated result copies.
It reproduces captured responses, not fresh inference. The model identifier is not
necessarily an immutable model version, and SHA-256 establishes compatibility,
not authenticity. Capture persistence assumes a single writer. Interrupted physical
writes can require manual intervention; exactly-once API billing is not guaranteed.
Publication of all four reports is not atomic. See the
[local replay instructions](../README.md#lesson-44--snapshot-backed-empirical-classification-replay).

### Supporting evidence

- [notebooks/01_uk_job_market_exploration.ipynb](../notebooks/01_uk_job_market_exploration.ipynb)
- [notebooks/02_salary_verification_replay.ipynb](../notebooks/02_salary_verification_replay.ipynb)
- [tests/fixtures/salary_evidence/observed_salary_evidence.csv](../tests/fixtures/salary_evidence/observed_salary_evidence.csv)
- [tests/analytics/test_offline_salary_replay.py](../tests/analytics/test_offline_salary_replay.py)

## 8. Limitations

- The exploratory sample contains only 60 first-page search results from one provider.
- Search-result selection and provider coverage may introduce systematic bias.
- Description excerpts may omit relevant information from full advertisements.
- Distinct advertisement IDs do not establish distinct underlying vacancies.
- Provider-predicted salaries are not independently verified advertised salaries.
- The eight-quotation benchmark is deliberately selected and non-representative.
- The exploratory population has not undergone complete LLM classification and extraction.
- External publication must comply with applicable data-redistribution terms.

The results should not be interpreted as estimates of UK-wide vacancy volumes, salary distributions or salary disclosure rates.

## 9. Conclusion

Trustworthy analytical outputs require more than successful data collection and information extraction.

Explicit provenance, deterministic validation, transparent exclusion criteria and reproducible analytical populations are essential to establishing what the available data can legitimately support.

The project demonstrates how LLM-assisted interpretation can be combined with conventional software engineering and analytical governance without transferring control of analytical policy to the LLM.

## 10. Future development

The longer-term UK Job Market Observatory will explore recurring data collection, additional data sources, longitudinal analysis and automated reporting.

These capabilities are outside the scope of the first portfolio release.

The Lesson 43 synthetic scenarios may also support the planned interactive advertisement walkthrough and an optional technical deep dive. This lesson implements neither website functionality nor runtime tracing; the publication target remains 15 December 2026.
