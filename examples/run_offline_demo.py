"""Run the public synthetic demonstration without external API calls."""

from pathlib import Path

from examples.synthetic_scenarios import (
    build_synthetic_postings,
    controlled_classification,
    controlled_salary_extraction,
)
from uk_job_market_agents.agents.batch_orchestration import (
    process_jobs,
)
from uk_job_market_agents.analytics.analytical_report import (
    build_analytical_report,
)
from uk_job_market_agents.analytics.analytical_report_csv import (
    write_analytical_report_csv,
)
from uk_job_market_agents.analytics.job_export import (
    build_job_export_rows,
)
from uk_job_market_agents.ingestion.offline_workflow import (
    run_offline_workflow,
)


def run_demo(output_dir: Path) -> None:
    """Execute synthetic scenarios and publish analytical reports."""

    postings = build_synthetic_postings()

    source_ids = {
        posting.raw_description: posting.source_id
        for posting in postings
    }

    def classifier(job):
        return controlled_classification(job.source_id)

    def salary_extractor(description):
        return controlled_salary_extraction(
            source_ids[description]
        )

    def processor(jobs):
        return process_jobs(
            jobs,
            classifier=classifier,
            salary_extractor=salary_extractor,
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    outcomes, summary = run_offline_workflow(
        postings,
        processor=processor,
        job_export_path=output_dir / "jobs.csv",
        summary_export_path=output_dir / "batch_summary.csv",
    )

    rows = build_job_export_rows(postings, outcomes)
    report = build_analytical_report(rows)

    write_analytical_report_csv(
        report,
        output_dir / "analytical_samples.csv",
        output_dir / "role_family_summary.csv",
    )

    print("Synthetic offline demonstration")
    print("--------------------------------")
    print("No live API or LLM calls.")
    print("Inputs and agent responses are synthetic.")
    print()
    print(summary.model_dump_json(indent=2))
    print()
    print(f"Role eligible: {report.samples.role_eligible.populated}")
    print(f"Salary eligible: {report.samples.salary_eligible.populated}")
    print(f"Reports written to: {output_dir}")


if __name__ == "__main__":
    run_demo(Path("data/processed/public_demo"))
