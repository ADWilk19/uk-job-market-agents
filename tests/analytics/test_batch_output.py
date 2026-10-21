from io import StringIO

from uk_job_market_agents.analytics.batch_output import (
    write_batch_summary_csv,
)
from uk_job_market_agents.analytics.batch_summary import BatchSummary


def test_batch_csv_writes_header():
    summary = BatchSummary(
        total=0,
        processed=0,
        review_required=0,
        failed=0,
    )

    output = StringIO()

    write_batch_summary_csv(summary, output)

    lines = output.getvalue().splitlines()

    assert lines[0] == (
        "total,processed,review_required,failed,"
        "processed_rate,review_rate,failure_rate"
    )


def test_batch_csv_writes_data_row():
    summary = BatchSummary(
        total=10,
        processed=7,
        review_required=2,
        failed=1,
    )

    output = StringIO()

    write_batch_summary_csv(summary, output)

    lines = output.getvalue().splitlines()

    assert lines[1] == (
        "10,7,2,1,0.700000,0.200000,0.100000"
    )


def test_batch_csv_writes_empty_batch():
    summary = BatchSummary(
        total=0,
        processed=0,
        review_required=0,
        failed=0,
    )

    output = StringIO()
    write_batch_summary_csv(summary, output)

    lines = output.getvalue().splitlines()

    assert lines[1] == (
        "0,0,0,0,0.000000,0.000000,0.000000"
    )


def test_batch_csv_output_is_deterministic():
    summary = BatchSummary(
        total=3,
        processed=1,
        review_required=1,
        failed=1,
    )

    first_output = StringIO()
    second_output = StringIO()

    write_batch_summary_csv(summary, first_output)
    write_batch_summary_csv(summary, second_output)

    assert first_output.getvalue() == second_output.getvalue()

    assert first_output.getvalue() == (
        "total,processed,review_required,failed,"
        "processed_rate,review_rate,failure_rate\n"
        "3,1,1,1,0.333333,0.333333,0.333333\n"
    )
