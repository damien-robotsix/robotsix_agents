"""
Task Organizer agent implementation.

This module provides the Task Organizer agent, which is responsible for managing a TODO list in a markdown file.
"""

import logging
from autogen_agentchat.agents import AssistantAgent
from robotsix_agents.core import get_config_manager, load_agent_config
from .tools import TodoManager

logger = logging.getLogger(__name__)


async def create_agent(working_directory: str = None) -> AssistantAgent:
    """
    Creates the Task Organizer agent with dedicated TODO list tools.
    """
    config_manager = get_config_manager()
    agent_config = load_agent_config("task_organizer") 
    model_client = config_manager.get_model_client("task_organizer")

    # Initialize the tool manager
    todo_manager = TodoManager(working_directory=working_directory)

    # Clean up any previous TODO file on instantiation
    todo_manager.delete_todo_file()

    # Add the initial task to check the Git branch
    todo_manager.add_todo(task="Check the git branch and create a new one if needed. Avoid working on 'main' or 'master'.")

    def finalize_and_terminate() -> str:
        """Deletes the TODO file and returns the TERMINATE keyword."""
        todo_manager.delete_todo_file()
        return "TERMINATE"

    # Register the tool methods
    tool_functions = [
        todo_manager.add_todo,
        todo_manager.list_todos,
        todo_manager.mark_task_done,
        finalize_and_terminate,
    ]

    system_message = agent_config.get("system_message", """You are a Task Organizer agent. You are the project manager for a team of specialist agents. Your responsibility is to manage the project's TODO list and direct the team.

**Your Workflow:**
1.  **Understand the Goal**: At the beginning of a project, the user will give you a goal. Your first job is to break that goal down into a series of actionable steps.
2.  **Create a TODO List**: Use the `add_todo` tool to create a task for each step. Be clear and concise in your task descriptions.
3.  **Direct the Team**: After creating the list, or whenever you are asked for the next step, you must:
    a. Use the `list_todos` tool to see the current status.
    b. Identify the **first incomplete task** (the one with `- [ ]`).
    c. State the task clearly to the team (e.g., "The next task is: [task description]"). This is your response.
4.  **Mark Tasks as Done**: As the team completes tasks, you will be called upon to mark them as complete using the `mark_task_done` tool.
5.  **Finalize**: After marking a task, re-check the list. If all tasks are marked with `- [x]`, your work is done. You must then call the `finalize_and_terminate` tool.

Your response should always be either the next task to be performed or the result of the `finalize_and_terminate` tool.
""".strip())

    assistant_agent = AssistantAgent(
        name="task_organizer",
        model_client=model_client,
        tools=tool_functions,
        max_tool_iterations=agent_config.get("max_tool_iterations", 20),
        system_message=system_message,
        description=agent_config.get("description", "An agent that manages a TODO list for the team using a dedicated TodoManager.")
    )

    logger.info("Successfully created Task Organizer agent with a TodoManager.")
    return assistant_agent
