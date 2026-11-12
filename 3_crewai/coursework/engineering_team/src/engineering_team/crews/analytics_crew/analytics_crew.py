import os

from crewai import LLM, Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv
from .models import TechnicalSpecification

load_dotenv()

openrouter_llm = LLM(
    model="openrouter/deepseek/deepseek-v4-flash-20260731",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


@CrewBase
class AnalyticsCrew:
    """Analytics Crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def team_lead_analytics(self) -> Agent:
        return Agent(
            config=self.agents_config["team_lead_analytics"],
            llm=openrouter_llm,
        )

    @agent
    def business_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["business_analyst"],
            llm=openrouter_llm,
            mcps=["https://mcp.exa.ai/mcp"],
        )

    @agent
    def system_analysis(self) -> Agent:
        return Agent(
            config=self.agents_config["system_analyst"],
            llm=openrouter_llm,
            mcps=[
                "https://mcp.exa.ai/mcp",
                "https://mcp.context7.com/mcp",
            ],
        )

    @task
    def business_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["business_analysis_task"],  # type: ignore[index]
        )

    @task
    def system_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["system_analysis_task"],
            context=[self.business_analysis_task()],
        )

    @task
    def technical_specification_task(self) -> Task:
        return Task(
            config=self.tasks_config["technical_specification_task"],
            context=[self.business_analysis_task(), self.system_analysis_task()],
            output_pydantic=TechnicalSpecification,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Analytics Crew"""
        return Crew(
            agents=[
                self.business_analyst(),
                self.system_analysis(),
            ],  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            verbose=True,
            manager_agent=self.team_lead_analytics(),
            process=Process.hierarchical,
        )
