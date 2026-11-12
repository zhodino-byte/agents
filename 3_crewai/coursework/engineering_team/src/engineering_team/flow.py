from typing import Literal

from pydantic import BaseModel, Field
from crewai.flow import Flow, listen, or_, router, start
from .crews.analytics_crew.models import TechnicalSpecification
from .crews.analytics_crew.analytics_crew import AnalyticsCrew
from .crews.developing_crew.development_crew import DevelopmentCrew
from .crews.developing_crew.models import DevelopmentHandoff
from .tools.sandbox_tools import reset_sandbox
from .crews.qa_crew.models import QAReport
from .crews.qa_crew.qa_crew import QACrew


class ProjectState(BaseModel):
    request: str = ""

    technical_spec: TechnicalSpecification | None = None
    development_handoff: DevelopmentHandoff | None = None
    qa_report: QAReport | None = None

    development_attempt: int = 0
    max_development_attempts: int = Field(
        default=1,
        ge=1,
    )

    sandbox_initialized: bool = False

    status: str = "pending"
    reason: str | None = None


class ProjectFlow(Flow[ProjectState]):

    @start()
    def run_analytics(self):
        if not self.state.request.strip():
            raise ValueError("Project request is empty")

        self.state.status = "analyzing"

        result = AnalyticsCrew().crew().kickoff(inputs={"request": self.state.request})

        if result.pydantic is None:
            raise ValueError("Analytics Crew did not return structured output")

        self.state.technical_spec = TechnicalSpecification.model_validate(
            result.pydantic
        )

    @router(run_analytics)
    def route_analytics(
        self,
    ) -> Literal["spec_ready", "spec_blocked"]:

        spec = self.state.technical_spec

        if spec is not None and spec.status == "ready" and not spec.blocking_questions:
            return "spec_ready"

        return "spec_blocked"

    @listen("spec_blocked")
    def handle_spec_blocked(self):
        self.state.status = "needs_clarification"

        return {
            "status": self.state.status,
            "questions": (
                self.state.technical_spec.blocking_questions
                if self.state.technical_spec
                else []
            ),
        }

    @listen("spec_ready")
    def initialize_sandbox(self):
        if self.state.sandbox_initialized:
            return

        reset_sandbox()

        self.state.sandbox_initialized = True
        self.state.development_attempt = 0

    @listen(or_(initialize_sandbox, "qa_retry"))
    def run_development(self):

        spec = self.state.technical_spec

        if spec is None:
            raise ValueError("Technical specification is missing")

        if not self.state.sandbox_initialized:
            raise RuntimeError("Sandbox is not initialized")

        self.state.development_attempt += 1
        self.state.status = "developing"

        is_fix = self.state.qa_report is not None

        feedback = (
            self.state.qa_report.model_dump_json(indent=2)
            if is_fix
            else "No previous QA feedback."
        )

        result = (
            DevelopmentCrew()
            .crew()
            .kickoff(
                inputs={
                    "technical_spec": spec.model_dump_json(indent=2),
                    "development_mode": ("fix" if is_fix else "initial"),
                    "qa_feedback": feedback,
                }
            )
        )

        if result.pydantic is None:
            raise ValueError("Development Crew did not return structured output")

        self.state.development_handoff = DevelopmentHandoff.model_validate(
            result.pydantic
        )

    @router(run_development)
    def route_development(
        self,
    ) -> Literal["dev_ready", "dev_blocked"]:

        handoff = self.state.development_handoff

        if handoff is not None and handoff.status == "ready_for_qa":
            return "dev_ready"

        return "dev_blocked"

    @listen("dev_blocked")
    def handle_dev_blocked(self):
        self.state.status = "development_blocked"

        return {
            "status": self.state.status,
            "handoff": (
                self.state.development_handoff.model_dump()
                if self.state.development_handoff
                else None
            ),
        }

    @listen("dev_ready")
    def run_qa(self):

        spec = self.state.technical_spec
        handoff = self.state.development_handoff

        if spec is None or handoff is None:
            raise ValueError("QA input is incomplete")

        self.state.status = "testing"

        # IMPORTANT: do not reset the sandbox

        result = (
            QACrew()
            .crew()
            .kickoff(
                inputs={
                    "technical_spec": spec.model_dump_json(indent=2),
                    "development_handoff": (handoff.model_dump_json(indent=2)),
                }
            )
        )

        if result.pydantic is None:
            raise ValueError("QA Crew did not return structured output")

        self.state.qa_report = QAReport.model_validate(result.pydantic)

    @router(run_qa)
    def route_qa(
        self,
    ) -> Literal[
        "qa_passed",
        "qa_retry",
        "qa_blocked",
        "qa_exhausted",
    ]:

        report = self.state.qa_report
        spec = self.state.technical_spec

        if report is None or spec is None:
            self.state.reason = "QA report or specification missing"
            return "qa_blocked"

        if report.status == "passed":

            required_ids = {req.id for req in spec.functional_requirements}

            verified_ids = {
                test.requirement_id
                for test in report.test_results
                if test.status == "passed" and test.requirement_id is not None
            }

            missing = required_ids - verified_ids

            if missing:
                self.state.reason = (
                    f"Requirements without passing tests: " f"{sorted(missing)}"
                )
                return "qa_blocked"

            return "qa_passed"

        if report.status == "blocked":
            self.state.reason = "QA execution is blocked"
            return "qa_blocked"

        # Failed QA: retry only within the configured limit
        if self.state.development_attempt < self.state.max_development_attempts:
            return "qa_retry"

        return "qa_exhausted"

    @listen("qa_passed")
    def complete_project(self):
        self.state.status = "completed"

        return {
            "status": "completed",
            "development_attempts": (self.state.development_attempt),
            "development_handoff": (self.state.development_handoff.model_dump()),
            "qa_report": self.state.qa_report.model_dump(),
        }

    @listen("qa_blocked")
    def handle_qa_blocked(self):
        self.state.status = "qa_blocked"

        return {
            "status": "qa_blocked",
            "reason": self.state.reason,
            "report": (
                self.state.qa_report.model_dump() if self.state.qa_report else None
            ),
        }

    @listen("qa_exhausted")
    def handle_retries_exhausted(self):
        self.state.status = "retries_exhausted"

        return {
            "status": "retries_exhausted",
            "attempts": self.state.development_attempt,
            "remaining_defects": [
                defect.model_dump() for defect in self.state.qa_report.defects
            ],
        }
