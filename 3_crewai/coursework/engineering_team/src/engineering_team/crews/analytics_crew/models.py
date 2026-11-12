from typing import Literal

from pydantic import BaseModel, Field, model_validator


class AcceptanceCriterion(BaseModel):
    id: str
    description: str


class FunctionalRequirement(BaseModel):
    id: str
    title: str
    description: str
    priority: Literal["must", "should", "could"]
    acceptance_criteria: list[AcceptanceCriterion] = Field(min_length=1)


class APIEndpoint(BaseModel):
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
    path: str
    description: str
    request_schema: str | None = Field(
        default=None,
        description="Request JSON Schema encoded as a JSON string, if applicable.",
    )
    response_schema: str | None = Field(
        default=None,
        description="Response JSON Schema encoded as a JSON string, if applicable.",
    )
    status: Literal["confirmed", "proposed"]


class TechnicalSpecification(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    delivery_mode: Literal["production", "prototype"] = "prototype"

    title: str
    business_goal: str

    scope: list[str] = Field(min_length=1)
    out_of_scope: list[str] = Field(default_factory=list)

    functional_requirements: list[FunctionalRequirement] = Field(min_length=1)

    api_endpoints: list[APIEndpoint] = Field(default_factory=list)
    data_entities: list[str] = Field(default_factory=list)
    integrations: list[str] = Field(default_factory=list)
    non_functional_requirements: list[str] = Field(default_factory=list)

    assumptions: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    blocking_questions: list[str] = Field(default_factory=list)

    status: Literal["ready", "needs_clarification"]

    @model_validator(mode="after")
    def validate_readiness(self):
        if self.status == "ready" and self.blocking_questions:
            raise ValueError(
                "Specification cannot be ready " "while blocking questions remain."
            )
        return self
