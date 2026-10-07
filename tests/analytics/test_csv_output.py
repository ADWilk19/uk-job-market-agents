import csv

from uk_job_market_agents.analytics.output import (
    SalaryAnalysisRow,
    write_salary_analysis_csv,
)


def test_write_salary_analysis_csv(tmp_path):
    rows = [
        SalaryAnalysisRow(
            dimension="overall",
            segment="all",
            records=5,
            records_with_salary=4,
            average_midpoint=52_500.0,
            has_sufficient_sample=True,
        ),
        SalaryAnalysisRow(
            dimension="role_family",
            segment="data_engineering",
            records=3,
            records_with_salary=2,
            average_midpoint=60_000.0,
            has_sufficient_sample=True,
        ),
    ]

    output_path = tmp_path / "salary_analysis.csv"

    write_salary_analysis_csv(rows, output_path)

    with output_path.open(newline="", encoding="utf-8") as file:
        written_rows = list(csv.DictReader(file))

    assert written_rows == [
        {
            "dimension": "overall",
            "segment": "all",
            "records": "5",
            "records_with_salary": "4",
            "average_midpoint": "52500.0",
            "has_sufficient_sample": "True",
        },
        {
            "dimension": "role_family",
            "segment": "data_engineering",
            "records": "3",
            "records_with_salary": "2",
            "average_midpoint": "60000.0",
            "has_sufficient_sample": "True",
        },
    ]


def test_write_salary_analysis_csv_handles_missing_average(tmp_path):
    rows = [
        SalaryAnalysisRow(
            dimension="role_family",
            segment="data_science",
            records=1,
            records_with_salary=0,
            average_midpoint=None,
            has_sufficient_sample=False,
        ),
    ]

    output_path = tmp_path / "salary_analysis.csv"

    write_salary_analysis_csv(rows, output_path)

    with output_path.open(newline="", encoding="utf-8") as file:
        written_rows = list(csv.DictReader(file))

    assert written_rows == [
        {
            "dimension": "role_family",
            "segment": "data_science",
            "records": "1",
            "records_with_salary": "0",
            "average_midpoint": "",
            "has_sufficient_sample": "False",
        },
    ]


def test_write_salary_analysis_csv_writes_header_when_rows_are_empty(tmp_path):
    output_path = tmp_path / "salary_analysis.csv"

    write_salary_analysis_csv([], output_path)

    with output_path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        written_rows = list(reader)

    assert reader.fieldnames == [
        "dimension",
        "segment",
        "records",
        "records_with_salary",
        "average_midpoint",
        "has_sufficient_sample",
    ]
    assert written_rows == []
