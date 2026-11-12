from .flow import ProjectFlow


def kickoff():
    flow = ProjectFlow()

    result = flow.kickoff(
        inputs={
            "request": """
            Create a Gradio NFL calendar application.

            Requirements:
            - User can see all NFL seaso matches
            - User can choose his favourite team
            - User can see the players
            
            """,
            "max_development_attempts": 1,
        }
    )

    print("Flow result:", result)
    print("Final status:", flow.state.status)
    print(
        "Development attempts:",
        flow.state.development_attempt,
    )


def plot():
    flow = ProjectFlow()
    flow.plot("project_flow")


if __name__ == "__main__":
    kickoff()
