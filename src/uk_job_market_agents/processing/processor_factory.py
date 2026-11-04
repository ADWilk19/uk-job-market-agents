"""Select processing implementations for the CLI."""

from uk_job_market_agents.agents.batch_orchestration import process_jobs


def create_processor(mode: str):
    """Return the batch processor for a supported execution mode."""
    if mode == "agent":
        return process_jobs

    raise ValueError(f"Unsupported processing mode: {mode}")
