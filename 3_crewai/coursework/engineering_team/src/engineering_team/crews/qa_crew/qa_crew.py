import os

from crewai import LLM, Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv
from ...tools.sandbox_tools import (
    list_sandbox_files,
    read_sandbox_file,
    run_sandbox_python,
    write_sandbox_file,
)
from .models import QAReport

load_dotenv()

openrouter_llm = LLM(
    model="openrouter/deepseek/deepseek-v4-flash-20260731",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


@CrewBase
class QACrew:

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def qa_lead(self) -> Agent:
        return Agent(
            config=self.agents_config["qa_lead"],
            llm=openrouter_llm,
        )

    @agent
    def functional_qa_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["functional_qa_engineer"],
            llm=openrouter_llm,
            tools=[
                list_sandbox_files,
                read_sandbox_file,
                run_sandbox_python,
            ],
        )

    @agent
    def qa_automation_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["qa_automation_engineer"],
            llm=openrouter_llm,
            tools=[
                list_sandbox_files,
                read_sandbox_file,
                write_sandbox_file,
                run_sandbox_python,
            ],
        )

    @task
    def functional_testing_task(self) -> Task:
        return Task(config=self.tasks_config["functional_testing_task"])

    @task
    def automated_testing_task(self) -> Task:
        return Task(
            config=self.tasks_config["automated_testing_task"],
            context=[self.functional_testing_task()],
        )

    @task
    def qa_review_task(self) -> Task:
        return Task(
            config=self.tasks_config["qa_review_task"],
            context=[
                self.functional_testing_task(),
                self.automated_testing_task(),
            ],
            output_pydantic=QAReport,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.functional_qa_engineer(),
                self.qa_automation_engineer(),
            ],
            tasks=[
                self.functional_testing_task(),
                self.automated_testing_task(),
                self.qa_review_task(),
            ],
            manager_agent=self.qa_lead(),
            process=Process.hierarchical,
            verbose=True,
            memory=False,
            cache=False,
        )
