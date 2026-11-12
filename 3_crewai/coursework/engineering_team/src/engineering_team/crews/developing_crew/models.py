from typing import Literal
from pydantic import BaseModel, Field, model_validator


class DevelopmentHandoff(BaseModel):
    status: Literal["ready_for_qa", "blocked"]

    implemented_requirement_ids: list[str] = Field(default_factory=list)

    modified_files: list[str] = Field(default_factory=list)

    entrypoint: str = "app.py"
    run_command: str = "uv run app.py"

    smoke_check_results: list[str] = Field(default_factory=list)

    known_issues: list[str] = Field(default_factory=list)

    blocking_questions: list[str] = Field(default_factory=list)

    handoff_notes: str = ""

    @model_validator(mode="after")
    def check_readiness(self):
        if self.status == "ready_for_qa" and self.blocking_questions:
            raise ValueError("Cannot hand off to QA with unresolved blockers.")

        return self
