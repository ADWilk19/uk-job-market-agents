import pytest

from uk_job_market_agents.agents.salary_review import (
    SalaryEvidence,
    parse_salary_evidence,
)
from uk_job_market_agents.models.salary import SalaryPeriod

@pytest.mark.parametrize(
    "evidence,expected",
    [
        (
            "£55,000.00 per year",
            SalaryEvidence(55000, 55000, SalaryPeriod.YEAR),
        ),
        (
            "Salary: £65,000–£80,000 per annum.",
            SalaryEvidence(65000, 80000, SalaryPeriod.YEAR),
        ),
    ],
)
def test_recognises_supported_salary_evidence(evidence, expected):
    assert parse_salary_evidence(evidence) == expected


@pytest.mark.parametrize(
    "evidence",
    [
        "£55,000 - £45,000",       # Reversed bounds
        "£0 - £55,000",            # Zero salary
        "£45,00 - £55,000",        # Malformed grouping
        "£45.50 - £55,000",        # Fractional pounds
        "£45.0009k - £55k",        # Fractional result
        "£45k - 55k",              # Missing second currency symbol
        "£45k - £55k per month",   # Unsupported period
        "£45k - £55k pa per day",  # Conflicting periods
        "£45k - £55k payroll",     # Invalid period suffix
        "£45kto£55k pa",
        "£45.0000000000000000000000000001k - £55k pa",
        "Approximately £55,000",  # Unsupported approximation wording
    ],
)
def test_rejects_unsupported_salary_evidence(evidence):
    assert parse_salary_evidence(evidence) is None
