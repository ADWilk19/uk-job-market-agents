from enum import Enum

from pydantic import (
    AwareDatetime,
    BaseModel,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)


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


class DescriptionCompleteness(str, Enum):
    COMPLETE = "complete"
    EXCERPT = "excerpt"
    UNKNOWN = "unknown"


class JobPosting(BaseModel):
    # Source fields
    source_id: str = Field(strict=True, min_length=1)
    source: str
    source_url: HttpUrl | None = None
    collected_at: AwareDatetime
    published_at: AwareDatetime | None = None

    # Raw input
    raw_title: str
    raw_description: str
    description_completeness: DescriptionCompleteness = (
        DescriptionCompleteness.UNKNOWN
    )
    location_raw: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    company_name: str | None = None
    contract_type_raw: str | None = None
    contract_time_raw: str | None = None
    source_category_raw: str | None = None

    # Classified / derived fields
    role_family: RoleFamily = RoleFamily.UNKNOWN
    seniority: Seniority = Seniority.UNKNOWN
    work_pattern: WorkPattern = WorkPattern.UNKNOWN

    # Salary
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    salary_currency: str = "GBP"

    # Provider-supplied salary metadata (not interpreted salary)
    source_salary_min: float | None = Field(default=None, ge=0)
    source_salary_max: float | None = Field(default=None, ge=0)
    source_salary_predicted: bool | None = None

    # Skills
    skills: list[str] = Field(default_factory=list)

    # Agent / QA metadata
    classification_confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )
    validation_status: ValidationStatus = ValidationStatus.UNVALIDATED

    @field_validator("source_id", "source")
    @classmethod
    def validate_source_fields(cls, value: str) -> str:
        """Reject empty or whitespace-only source fields."""
        if not value.strip():
            raise ValueError("Source fields must not be empty")

        return value

    @field_validator("raw_title", "raw_description")
    @classmethod
    def validate_raw_content(cls, value: str) -> str:
        """Reject empty or whitespace-only advertisement content."""
        if not value.strip():
            raise ValueError("Advertisement content must not be empty")

        return value

    @model_validator(mode="after")
    def validate_salary_range(self):
        """Ensure interpreted and provider salary ranges are ordered."""
        for minimum, maximum in (
            (self.salary_min, self.salary_max),
            (self.source_salary_min, self.source_salary_max),
        ):
            if (
                minimum is not None
                and maximum is not None
                and minimum > maximum
            ):
                raise ValueError("Salary minimum cannot exceed maximum")

        return self

    @model_validator(mode="after")
    def validate_coordinate_pair(self):
        """Require either a complete coordinate pair or neither coordinate."""
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError(
                "Latitude and longitude must both be provided or both be absent"
            )

        return self
