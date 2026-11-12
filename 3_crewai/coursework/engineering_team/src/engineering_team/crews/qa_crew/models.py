from typing import Literal

from pydantic import BaseModel, Field, model_validator


class QATestResult(BaseModel):
    test_id: str
    requirement_id: str | None = None
    description: str

    status: Literal[
        "passed",
        "failed",
        "blocked",
        "not_run",
    ]

    evidence: str = Field(min_length=1)
    test_file: str | None = None


class Defect(BaseModel):
    id: str
    requirement_id: str | None = None

    severity: Literal[
        "critical",
        "high",
        "medium",
        "low",
    ]

    summary: str
    steps_to_reproduce: list[str]
    expected_behavior: str
    actual_behavior: str
    evidence: str


class QAReport(BaseModel):
    status: Literal["passed", "failed", "blocked"]
    delivery_mode: Literal["production", "prototype"]

    tested_requirement_ids: list[str] = Field(default_factory=list)

    test_results: list[QATestResult] = Field(min_length=1)

    defects: list[Defect] = Field(default_factory=list)

    untested_requirement_ids: list[str] = Field(default_factory=list)

    blockers: list[str] = Field(default_factory=list)

    recommendations: list[str] = Field(default_factory=list)

    summary: str

    @model_validator(mode="after")
    def validate_status(self):
        if self.status == "passed":
            if any(test.status != "passed" for test in self.test_results):
                raise ValueError("All test results must pass " "for QA to be approved.")

            if self.defects or self.blockers or self.untested_requirement_ids:
                raise ValueError(
                    "QA cannot pass with defects, "
                    "blockers, or untested requirements."
                )

        if self.status == "failed" and not self.defects:
            raise ValueError("Failed QA must include confirmed defects.")

        return self
