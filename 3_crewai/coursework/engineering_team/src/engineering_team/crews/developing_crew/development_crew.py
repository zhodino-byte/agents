import os

from crewai import LLM, Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv
from ...tools.sandbox_tools import sandbox_tools
from .models import DevelopmentHandoff

load_dotenv()

openrouter_llm = LLM(
    model="openrouter/deepseek/deepseek-v4-flash-20260731",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


@CrewBase
class DevelopmentCrew:

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def development_lead(self) -> Agent:
        return Agent(
            config=self.agents_config["development_lead"],
            llm=openrouter_llm,
        )

    @agent
    def backend_developer(self) -> Agent:
        return Agent(
            config=self.agents_config["backend_developer"],
            llm=openrouter_llm,
            tools=sandbox_tools,
            mcps=[
                "https://mcp.context7.com/mcp",
            ],
        )

    @agent
    def frontend_developer(self) -> Agent:
        return Agent(
            config=self.agents_config["frontend_developer"],
            llm=openrouter_llm,
            tools=sandbox_tools,
            mcps=[
                "https://gradio-docs-mcp.hf.space/gradio_api/mcp/",
                "https://mcp.context7.com/mcp",
            ],
        )

    @task
    def backend_implementation_task(self) -> Task:
        return Task(config=self.tasks_config["backend_implementation_task"])

    @task
    def frontend_implementation_task(self) -> Task:
        return Task(
            config=self.tasks_config["frontend_implementation_task"],
            context=[self.backend_implementation_task()],
        )

    @task
    def development_handoff_task(self) -> Task:
        return Task(
            config=self.tasks_config["development_handoff_task"],
            context=[
                self.backend_implementation_task(),
                self.frontend_implementation_task(),
            ],
            output_pydantic=DevelopmentHandoff,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.backend_developer(),
                self.frontend_developer(),
            ],
            tasks=[
                self.backend_implementation_task(),
                self.frontend_implementation_task(),
                self.development_handoff_task(),
            ],
            manager_agent=self.development_lead(),
            process=Process.hierarchical,
            verbose=True,
            memory=False,
            cache=False,
        )
