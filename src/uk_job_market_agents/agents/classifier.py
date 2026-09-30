from openai import OpenAI
from pydantic import BaseModel

from uk_job_market_agents.models.job_posting import RoleFamily, WorkPattern


class ClassificationResult(BaseModel):
    role_family: RoleFamily
    work_pattern: WorkPattern
    reasoning: str


def classify_with_llm(title: str, description: str) -> ClassificationResult:
    return _call_model(title, description)


def test_classify_with_llm_returns_structured_result(monkeypatch):
    expected = ClassificationResult(
        role_family=RoleFamily.DATA_SCIENCE,
        work_pattern=WorkPattern.HYBRID,
        reasoning=(
            "The role is focused on forecasting and optimisation, "
            "with mandatory office attendance twice per week."
        ),
    )

    def fake_model_call(title: str, description: str) -> ClassificationResult:
        return expected

    monkeypatch.setattr(
        "uk_job_market_agents.agents.classifier._call_model",
        fake_model_call,
    )

    result = classify_with_llm(
        "Data Scientist",
        (
            "This is a remote-first role. "
            "All team members must attend the Manchester office "
            "every Tuesday and Thursday."
        ),
    )

    assert result == expected


def _call_model(title: str, description: str) -> ClassificationResult:
    client = OpenAI()

    prompt = f"""
Classify the following UK job advert.

Use only the allowed enum values provided by the response schema.

Role title:
{title}

Description:
{description}

Interpret the actual working arrangement, not just isolated keywords.
For example, mandatory recurring office attendance should affect the
work-pattern classification even if the advert describes itself as
remote-first.
"""

    response = client.responses.parse(
        model="gpt-5.6-luna",
        input=prompt,
        text_format=ClassificationResult,
    )

    result = response.output_parsed

    if result is None:
        raise RuntimeError("Model did not return a parsed classification")

    return result
