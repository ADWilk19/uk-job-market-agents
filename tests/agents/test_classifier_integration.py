import os

import pytest

from uk_job_market_agents.agents.classifier import classify_with_llm
from uk_job_market_agents.models.job_posting import (
    RoleFamily,
    WorkPattern,
)


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not configured",
)
def test_llm_classifies_remote_first_hybrid_role():
    result = classify_with_llm(
        "Data Scientist",
        """This is a remote-first role.

        You will build forecasting and optimisation models using Python,
        pandas, scikit-learn and SQL.

        All members of the team are expected to attend our Manchester
        office every Tuesday and Thursday.""",
    )

    assert result.role_family == RoleFamily.DATA_SCIENCE
    assert result.work_pattern == WorkPattern.HYBRID
