from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class RoleFamily(str, Enum):
    DATA_ENGINEERING = "data_engineering"
    ANALYTICS_ENGINEERING = "analytics_engineering"
    DATA_SCIENCE = "data_science"
    DATA_ANALYTICS = "data_analytics"
    BUSINESS_INTELLIGENCE = "business_intelligence"
    MACHINE_LEARNING = "machine_learning"
    SOFTWARE_ENGINEERING = "software_engineering"
    OTHER = "other"
    UNKNOWN = "unknown"


class Seniority(str, Enum):
    INTERN = "intern"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    MANAGER = "manager"
    DIRECTOR = "director"
    UNKNOWN = "unknown"


class WorkPattern(str, Enum):
    ONSITE = "onsite"
    HYBRID = "hybrid"
    REMOTE = "remote"
    UNKNOWN = "unknown"


class ValidationStatus(str, Enum):
    UNVALIDATED = "unvalidated"
    VALID = "valid"
    NEEDS_REVIEW = "needs_review"
    INVALID = "invalid"


class JobPosting(BaseModel):
    # Source fields
    source_id: str
    source: str
    collected_at: datetime

    # Raw input
    raw_title: str
    raw_description: str
    location_raw: str | None = None

    # Classified / derived fields
    role_family: RoleFamily = RoleFamily.UNKNOWN
    seniority: Seniority = Seniority.UNKNOWN
    work_pattern: WorkPattern = WorkPattern.UNKNOWN

    # Salary
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    salary_currency: str = "GBP"

    # Skills
    skills: list[str] = Field(default_factory=list)

    # Agent / QA metadata
    classification_confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )
    validation_status: ValidationStatus = ValidationStatus.UNVALIDATED

    @model_validator(mode="after")
    def validate_salary_range(self):
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_min > self.salary_max
        ):
            raise ValueError(
                "salary_min cannot be greater than salary_max"
            )

        return self
