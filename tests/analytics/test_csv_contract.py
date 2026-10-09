from uk_job_market_agents.analytics.output import (
    SalaryAnalysisRow,
    write_salary_analysis_csv,
)

def test_csv_uses_lf_line_endings(tmp_path):
    rows = [
        SalaryAnalysisRow(
            dimension="overall",
            segment="all",
            records=2,
            records_with_salary=2,
            average_midpoint=70000.0,
            has_sufficient_sample=True,
        )
    ]

    output_path = tmp_path / "salary_analysis.csv"

    write_salary_analysis_csv(rows, output_path)

    contents = output_path.read_bytes()

    assert b"\r\n" not in contents
    assert b"\n" in contents


def test_identical_rows_produce_identical_csv_bytes(tmp_path):
    rows = [
        SalaryAnalysisRow(
            dimension="overall",
            segment="all",
            records=2,
            records_with_salary=2,
            average_midpoint=70000.0,
            has_sufficient_sample=True,
        )
    ]

    first_path = tmp_path / "first.csv"
    second_path = tmp_path / "second.csv"

    write_salary_analysis_csv(rows, first_path)
    write_salary_analysis_csv(rows, second_path)

    assert first_path.read_bytes() == second_path.read_bytes()


def test_missing_salary_midpoint_is_empty(tmp_path):
    rows = [
        SalaryAnalysisRow(
            dimension="work_pattern",
            segment="remote",
            records=5,
            records_with_salary=0,
            average_midpoint=None,
            has_sufficient_sample=False,
        )
    ]

    output_path = tmp_path / "missing_salary.csv"

    write_salary_analysis_csv(rows, output_path)

    lines = output_path.read_text(encoding="utf-8").splitlines()

    assert lines[1] == "work_pattern,remote,5,0,,False"
