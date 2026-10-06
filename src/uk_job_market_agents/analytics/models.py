from pydantic import BaseModel, model_validator

from uk_job_market_agents.models.job_posting import (
    RoleFamily,
    WorkPattern,
)


class AnalyticalJobRecord(BaseModel):
    title: str
    role_family: RoleFamily
    work_pattern: WorkPattern
    salary_min: int | None = None
    salary_max: int | None = None

    @model_validator(mode="after")
    def validate_salary_range(self):
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_min > self.salary_max
        ):
            raise ValueError("salary_min cannot exceed salary_max")

        return self


    @property
    def salary_midpoint(self) -> float | None:
        if self.salary_min is None or self.salary_max is None:
            return None

        return (self.salary_min + self.salary_max) / 2
