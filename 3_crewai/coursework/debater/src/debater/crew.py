import os

from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from dotenv import load_dotenv

load_dotenv()

openrouter_llm = LLM(
    model="openrouter/openai/gpt-4o-mini",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


@CrewBase
class Debater:
    """Debater crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended

    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def debater(self) -> Agent:
        return Agent(
            config=self.agents_config["debater"],  # type: ignore[index]
            llm=openrouter_llm,
            verbose=True,
        )

    @agent
    def judge(self) -> Agent:
        return Agent(
            config=self.agents_config["judge"],  # type: ignore[index]
            llm=openrouter_llm,
            verbose=True,
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def propose(self) -> Task:
        return Task(
            config=self.tasks_config["propose"], output_file="output/propose.md"
        )

    @task
    def oppose(self) -> Task:
        return Task(
            config=self.tasks_config["oppose"],  # type: ignore[index]
            output_file="output/oppose.md",
        )

    @task
    def decide(self) -> Task:
        return Task(
            config=self.tasks_config["decide"],  # type: ignore[index]
            output_file="output/report.md",
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Debater crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
