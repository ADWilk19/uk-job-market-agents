# From Job Advertisements to Trustworthy Analytics

*An agent-assisted data pipeline for evaluating UK job advertisements sourced from Adzuna.*

**Status:** Working manuscript — Lesson 42 evidence review completed; publication requirements remain open
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

## 7. Reproducibility

The project uses saved API responses, labelled evidence fixtures, version-controlled implementations and automated regression tests.

Notebook 02 loads the original range-parser definitions from the full commit IDs corresponding to `f2f2f86` and `5f37e1f`, independently of the working production package. Both Git objects must be available locally. The Lesson 39/40 historical results above are separately attributed to their commits.

The exploratory notebooks and controlled salary replay can be executed without live API or LLM credentials when the required local inputs are available.

Raw responses in `data/raw/` are excluded from Git. A public checkout alone cannot reproduce these snapshot-based results. Missing snapshots cause notebook loading to fail; snapshot-dependent tests skip rather than retrieve new data, and a skip is not a reproduced measurement. Dependencies and the required Git history must also be available. See the [notebook setup instructions](../README.md#reproduce-the-notebook-offline) and [Lesson 41 replay procedure](../README.md#lesson-41--controlled-offline-salary-verification-replay).

**Outstanding publication considerations:** confirm applicable Adzuna data-redistribution permissions and attribution requirements before publishing source data or excerpts; establish and document a compliant way for readers to access the required evidence and reproduce the workflow. This review does not establish redistribution clearance or complete public reproducibility. End-to-end offline classification, report counts, exclusions and denominators still need reconciliation under the [release Definition of Done](../COURSE_PROGRESS.md#definition-of-done--first-portfolio-release).

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
