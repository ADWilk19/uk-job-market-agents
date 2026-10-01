from pydantic import BaseModel

from uk_job_market_agents.models.job_posting import (
    RoleFamily,
    WorkPattern,
)


class ResolvedClassification(BaseModel):
    role_family: RoleFamily
    work_pattern: WorkPattern
