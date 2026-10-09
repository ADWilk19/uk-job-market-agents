from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class SalaryPeriod(str, Enum):
    YEAR = "year"
    DAY = "day"
    HOUR = "hour"


class SalaryQuote(BaseModel):
    salary_min: int | None = Field(
        default=None,
        gt=0,
        strict=True,
    )
    salary_max: int | None = Field(
        default=None,
        gt=0,
        strict=True,
    )

    period: SalaryPeriod
    currency: Literal["GBP"] = "GBP"

    @model_validator(mode="after")
    def validate_bounds(self):
        if self.salary_min is None and self.salary_max is None:
            raise ValueError(
                "At least one salary bound is required"
            )

        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_min > self.salary_max
        ):
            raise ValueError(
                "salary_min cannot exceed salary_max"
            )

        return self
