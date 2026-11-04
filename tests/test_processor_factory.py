import pytest

from uk_job_market_agents.processing.processor_factory import (
    create_processor,
)
from uk_job_market_agents.agents.batch_orchestration import process_jobs


def test_processor_factory_selects_agent_batch_processor():
    processor = create_processor("agent")

    assert processor is process_jobs

def test_processor_factory_rejects_unknown_mode():
    with pytest.raises(ValueError, match="Unsupported processing mode"):
        create_processor("unknown")
