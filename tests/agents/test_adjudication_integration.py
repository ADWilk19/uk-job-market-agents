import os

import pytest

from uk_job_market_agents.agents.adjudication import (
    adjudicate_work_pattern,
)
from uk_job_market_agents.models.job_posting import WorkPattern


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not configured",
)
def test_live_work_pattern_adjudication():
    result = adjudicate_work_pattern(
        title="Data Scientist",
        description=(
            "This is a remote-first role. "
            "All members of the team are expected to attend "
            "our Manchester office every Tuesday and Thursday."
        ),
        rules_value=WorkPattern.REMOTE,
        llm_value=WorkPattern.HYBRID,
    )

    assert result.recommended_value == WorkPattern.HYBRID
