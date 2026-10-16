# UK Job Market Agents — Course Progress

**Status:** Active
**Last updated:** 16 October 2026
**Repository:** `uk-job-market-agents`
**Purpose:** A practical, test-driven Python course for building AI-assisted analysis of UK job advertisements, with a focus on data engineering, data science, data analytics and analytics engineering.

> **Source of truth:** This is a course handover assembled from our working sessions, not an automated audit of the repository. Confirm exact lesson numbers, branches and test counts with Git before treating them as definitive.

## 1. Learning goals

- Become more confident with Python development environments, package structure, Git, and tests.
- Learn when deterministic rules outperform LLMs, when LLMs help, and how to evaluate both.
- Build reusable agents and analysis workflows for real UK job-market data.
- Produce explainable, validated outputs that can inform a practical job search.
- Work in small steps: understand the concept, write or adjust tests, implement, run the suite, review and commit.

## 2. Current technical baseline

| Area | Current understanding |
| ---- | --------------------- |
| Language | Python 3.10.20 |
| Environment | Local `.venv` |
| Project packaging | `pyproject.toml` |
| Main dependency | `pydantic>=2,<3` |
| Tests | `pytest`, with `src` on `pythonpath` and `tests` as test path |
| Version control | Git; remote repository with `main` and lesson branches |
| Data | Five hand-labelled (“golden”) job adverts used for early evaluation |
| Model use | OpenAI API integrated for LLM classification and salary extraction |
| Secrets | `secrets.json` excluded from Git via `.gitignore` |

Most recently shared `pyproject.toml`:

```toml
[project]
name = "uk-job-market-agents"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "pydantic>=2,<3",
]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

**Environment note:** We have previously needed to reinstall `pytest` in the virtual environment. Before a lesson, confirm the active interpreter and dependencies rather than assuming they are installed.

## 3. Curriculum and progress

The table is organised by **topic**, not an asserted canonical lesson numbering. Use Git history and existing lesson branches to reconcile the original numbering.

| Topic | Status | Evidence / outcomes |
|---|---|---|
| Project foundations and domain models | Completed | Job-advert models and enumerations established. |
| Deterministic classification | Completed | Rules classify `WorkPattern` and `RoleFamily`. |
| LLM-based classification | Completed | OpenAI API connected; `classify_with_llm` issue resolved; API quota issue resolved. |
| Rules vs LLM comparison | Completed | CLI comparison output developed and formatted. |
| Evaluation metrics | Completed | Accuracy and disagreement measures added. |
| Disagreement analysis | Completed | Investigation of differing predictions and their causes. |
| Lesson 7 — Analytics integration | Completed | Deterministic salary summaries, guarded comparisons and analysis-ready output rows. |
| Lesson 8 — CSV export | Completed | Deterministic salary analysis CSV serialization. |
| Lesson 9 — Salary contract | Completed | SalaryQuote, SalaryPeriod and annual salary eligibility policy. |
| Lesson 10 — Portfolio hardening | Completed | CSV contract regression tests, documentation and GitHub Actions CI. |
| Lesson 11 — Salary extraction | Completed | Evidence-grounded extraction, deterministic verification and review states. |
| Lesson 12 — Salary extraction CSV and integration | Completed | Auditable extraction CSV, salary eligibility policy and analytics integration tests; commit `ce6deed`. |
| Lesson 13 — Company and location contracts | Completed | Company and raw location preserved in analytical contracts; commit `5c899ae`. |
| Lesson 14 — Orchestration | Completed | Single-job classification, salary verification and analytical record construction through `process_job()`; commit `6dc5650`. |
| Lesson 15 — Batch Orchestration and Processing Outcomes | Next; not implemented | Extend single-job orchestration to batches and explicit processing outcomes. |

### Domain vocabulary

`WorkPattern`: `REMOTE`, `HYBRID`, `ONSITE`, `UNKNOWN`.

`RoleFamily`: `data_engineering`, `data_science`, `data_analytics`, `analytics_engineering`.

The five initial labelled adverts included data engineering, data science and data analyst examples, covering remote and hybrid arrangements.

### Early evaluation example

On five golden adverts (a **small teaching set**, not a statistically robust benchmark):

| Measure | Rules | LLM |
|---|---:|---:|
| Role-family accuracy | 5/5 (100%) | 4/5 (80%) |
| Work-pattern accuracy | 4/5 (80%) | 5/5 (100%) |
| Full-record accuracy | 4/5 (80%) | 4/5 (80%) |

Observed disagreement rate: **40%**. These results describe one early evaluation run and should not be presented as general model performance.

### CSV export contract

The `write_salary_analysis_csv` export was documented to use this column order:

```csv
dimension,segment,records,records_with_salary,average_midpoint,has_sufficient_sample
```

Design expectations: deterministic ordering/output, consistent schema, and explicit handling of insufficient sample sizes. Confirm the exact implementation and handling of empty data against `output.py` and its tests.

## 4. Git and testing history

### Branch history

| Branch | Purpose |
| --- | --- |
| `main` | Stable integration branch |
| `lesson/05-evaluation-metrics` | Classification evaluation metrics |
| `lesson/06-disagreement-analyis` | Disagreement analysis |
| `lesson/07-analytics-integration` | Salary analytics and output rows |
| `lesson/08-csv-export` | CSV serialization |
| `lesson/09-salary-contract` | Salary validation and eligibility policy |
| `lesson/10-output-contract-ci` | CSV contract tests and GitHub Actions |
| `lesson/11-salary-extraction` | Evidence-grounded salary extraction |
| `lesson/12-salary-extraction-csv` | Salary extraction CSV and analytics eligibility integration |
| `lesson/13-company-location-contracts` | Company and location metadata contracts |
| `lesson/14-orchestration` | Single-job classification and salary orchestration |

**Current working branch:** `main`

**Stable baseline:** `6dc5650` (`feat: orchestrate classification and salary verification`).
Lessons 12–14 were committed and pushed on their lesson branches. The
verified comparison was `0 8` for `main...lesson/14-orchestration`; `main`
was then fast-forwarded from `4394860` to `6dc5650` and pushed to
`origin/main`. Lesson branches are retained as course checkpoints.

### Testing history

Earlier milestones included 24, 27 and 44 passing tests, each with one expected failure.

The latest confirmed full-suite result is **139 passed, 1 xfailed**
(16 October 2026, after integrating Lesson 14 into `main`).

This full regression run covers the completed Lessons 12–14. The earlier
Lesson 11 milestone was **111 passed, 1 xfailed** (13 October 2026).
The latest result was reported from `python -m pytest -q` before the
successful push of `main` to `origin/main`.

## 5. Recommended next-session verification

Run from the repository root:

```bash
git status --short --branch
git log -5 --oneline
git branch --all
python --version
python -m pytest -q
```

Then inspect `README.md`, `pyproject.toml`, the `src/` and `tests/` layout, and the single-job orchestrator before starting Lesson 15. The recorded baseline is `main` at `6dc5650`; check for subsequent changes.

**Do not make changes solely to reconcile this document.** Correct this document to match the repository where they differ.

## 6. Proposed next milestones

**Next lesson:** Lesson 15 — Batch Orchestration and Processing Outcomes.
Batch processing has not yet been implemented.

1. Start Lesson 15 from the tested, pushed `main` baseline at `6dc5650`.
2. Extend single-job orchestration to batches and define explicit processing outcomes.
3. Preserve the distinction between classification review and salary review, with meaningful tests for batch behaviour.
4. Subsequently acquire and validate real UK job advertisements, develop provenance and a comprehensive record-level export, and explore job-market trends. These remain future milestones.
5. Update README and this progress file at each completed milestone.

## 7. Working agreement for future lessons

- Teach concepts before presenting implementation.
- Prefer incremental exercises that I can attempt myself; provide guidance and code review rather than doing everything for me.
- Explain errors and trade-offs, including why a fix works.
- Use small, verifiable changes and run the focused test before the full suite.
- Keep explicit track of virtual-environment and dependency setup.
- Never assume a test passes unless output confirms it.
- Finish each lesson with: **what we learned**, **files changed**, **test results**, **Git branch/commit**, and **next step**.
- Preserve existing functionality; avoid unrelated refactors.
- Flag uncertainty rather than invent repository state.

## 8. ChatGPT Project setup brief

**Suggested Project name:** UK Job Market Agents

**Suggested Project instructions (copy into Project Instructions):**

> Act as my patient, technically rigorous Python and AI-agents tutor for the `uk-job-market-agents` course. I am developing my skills through a real UK job-advert classification and analytics project. Explain the objective and relevant concepts first, then lead me through small implementation steps. Encourage me to write the code, use tests to validate each increment, and help me debug errors from the actual terminal output. Maintain continuity with `COURSE_PROGRESS.md`, the repository and README, but do not assume this summary is more authoritative than the current code. Use accurate terminology, be candid about mistakes, and avoid unnecessary complexity. At the end of each lesson, give me a concise summary of progress, test status, commit status and the next starting point. Keep one chat per lesson and a separate chat for course planning.

**Suggested chat organisation:**

- `00 — Course Overview & Roadmap`
- `01+ — One chat per lesson` (numbered from the **verified** curriculum)
- `Troubleshooting — Environment, Git & tooling`
- `Architecture & Decisions — Cross-lesson design topics` (optional)

Historical chats can be moved into the Project for reference. New lessons should start in fresh chats and refer back to this document.

## 9. Lesson handover template

Complete this at the end of **each** new lesson:

```markdown
### Lesson NN — Title
- Date:
- Branch / commit:
- Objective:
- Concepts learned:
- Files changed:
- Focused tests:
- Full-suite result:
- Decisions / trade-offs:
- Remaining issues:
- Next lesson starting point:
```

### Lesson 11 — LLM Salary Extraction and Verification

**Status:** Complete

- Introduced `SalaryExtractionResult` for structured LLM output.
- Implemented OpenAI salary extraction using structured responses.
- Added deterministic verification of salary values, periods and
  supporting evidence.
- Introduced `SalaryReviewStatus`:
  `VERIFIED`, `REVIEW_REQUIRED`, `NOT_DISCLOSED`.
- Implemented `run_salary_workflow()` to coordinate extraction
  and verification.
- Added mocked API tests, workflow tests and regression coverage.
- Completed a live OpenAI smoke test using an annual salary range.
- Improved evidence parsing to support a salary label and trailing
  punctuation without relaxing full-string matching.

**Validation:** 111 passed, 1 xfailed (2026-10-13).

**Next:** Lesson 12 — Salary extraction CSV output and integration
with the existing analytics pipeline.

### Lesson 12 — Salary Extraction CSV and Analytics Integration

**Status:** Complete

**Branch / commit:** `lesson/12-salary-extraction-csv` / `ce6deed`; pushed and integrated into `main`.

- Implemented an auditable, deterministic salary extraction CSV exporter.
- Added eligibility checks for verified annual GBP salary ranges.
- Excluded unverified, daily-rate, and incomplete salary ranges from annual analytics.
- Integrated salary assessments with `AnalyticalJobRecord`.
- Confirmed that ineligible salaries do not affect aggregate statistics.
- Added parametrized eligibility tests and integration tests.
- Updated the README to document the new contracts and limitations.

**Validation:** Covered by the latest full-suite result of 139 passed,
1 xfailed after Lesson 14 integration.

**Next:** Lesson 13 — Company and location contracts (completed below).

### Lesson 13 — Company and Location Contracts

**Status:** Complete

**Branch / commit:** `lesson/13-company-location-contracts` / `5c899ae`; pushed and integrated into `main`.

- Preserved `company_name` and `location_raw` in analytical contracts.
- Added model and record-builder regression coverage for this metadata.
- Established the metadata contract subsequently used by `process_job()`.

**Validation:** Covered by the latest full-suite result of 139 passed,
1 xfailed after Lesson 14 integration.

**Next:** Lesson 14 — Orchestration (completed below).

### Lesson 14 — Orchestration

**Status:** Complete

**Branch / commit:** `lesson/14-orchestration` / `6dc5650`; pushed, fast-forwarded into `main`, and pushed to `origin/main`.

- Implemented `process_job(job: JobPosting) -> OrchestrationResult` to
  coordinate classification, salary verification and record construction.
- Runs classification on the raw title and description, resolves the
  classification, then attempts to build the analytical record.
- Passes `company_name` and `location_raw` from the job to the record builder.
- Stops before salary extraction when classification review is required
  or no resolved classification is available.
- For approved advertisements, runs salary extraction and verification on
  the raw description and applies the assessment to the analytical record.
- Returns the classification resolution plus optional analytical record
  and salary assessment. Both optional fields are `None` when classification
  prevents record construction.
- Added orchestration tests covering the single-job workflow.

**Decisions / trade-offs:** Classification review prevents an analytical
record and skips salary processing. Salary review does not exclude an
otherwise approved advertisement. Only verified, complete GBP annual
salary ranges populate annual salary fields; review-required,
not-disclosed and ineligible salaries remain excluded from annual salary
statistics while approved advertisements remain in job counts.

**Validation:** 139 passed, 1 xfailed (16 October 2026), on `main` after
fast-forward integration and before the successful push.

**Remaining limitations:** Single-job orchestration is implemented; batch
processing and real UK job-advert ingestion are not. Analytical records
do not preserve original salary quotations. A comprehensive record-level
export combining classifications, salary assessments and provenance is
still outstanding; the existing salary extraction audit CSV remains a
separate export.

**Next:** Lesson 15 — Batch Orchestration and Processing Outcomes.

## 10. Open housekeeping items

- [x] Complete Lesson 12 regression validation, commit and push.
- [x] Complete and push Lessons 13 and 14.
- [x] Verify that `process_job()` applies salary assessments and eligibility to approved analytical records.
- [x] Fast-forward `main` to `6dc5650`, run the full suite (139 passed, 1 xfailed), and push to `origin/main`.
- [ ] Commit and push the README and course-progress documentation refresh.
- [ ] Start Lesson 15 — Batch Orchestration and Processing Outcomes from the stable baseline.
