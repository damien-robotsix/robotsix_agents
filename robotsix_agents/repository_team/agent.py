"""
Repository Team agent implementation using SelectorGroupChat.

This module provides a Repository Team agent that coordinates coding specialist
and git agents using SelectorGroupChat from AutoGen AgentChat.
"""

import logging

from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from robotsix_agents.core import get_config_manager, load_agent_config
from .coding_specialist import agent as coding_specialist_agent
from .git import agent as git_agent
from .repository_specialist import agent as repository_specialist_agent
from .task_organizer import agent as task_organizer_agent

logger = logging.getLogger(__name__)


async def create_agent(*paths: str) -> SelectorGroupChat:
    """
    Create a Repository Team instance using SelectorGroupChat.

    This function creates a team of coding specialist and git agents that work together
    to handle repository operations. The team uses SelectorGroupChat to coordinate
    between the agents.

    Args:
        *paths: A list of repository paths. The first path is the primary
                repository, and any subsequent paths are treated as additional
                dependencies for which repository_specialist agents will be created.

    Returns:
        Configured Repository Team SelectorGroupChat
    """
    if not paths:
        raise ValueError("At least one repository path must be provided for the repository_team.")

    repository_directory = paths[0]
    additional_paths = paths[1:]

    # Get configuration manager
    config_manager = get_config_manager()

    # Get model client from configuration manager
    model_client = config_manager.get_model_client("repository_team")

    # Create coding specialist agent
    coding_specialist_assistant = await coding_specialist_agent.create_agent(
        working_directory=repository_directory
    )

    # Create git agent
    git_assistant = await git_agent.create_agent(
        repository_directory=repository_directory
    )

    # Create main repository specialist
    repository_specialists = [
        await repository_specialist_agent.create_agent(
            repository_directory=repository_directory
        )
    ]
    # Create repository specialists for additional paths
    if additional_paths:
        for path in additional_paths:
            repository_specialists.append(
                await repository_specialist_agent.create_agent(
                    repository_directory=path
                )
            )

    # Create task organizer agent
    task_organizer_assistant = await task_organizer_agent.create_agent(
        working_directory=repository_directory
    )

    description = (
        f"A team of agents for coordinating repository tasks in "
        f"{repository_directory}. Includes coding specialist with filesystem "
        f"operations, git operations, and semantic search capabilities."
    )

    # Team name with short repository path
    repository_name = repository_directory.split("/")[-1]
    team_name = f"repository_team_{repository_name}"

    # Create termination condition
    termination_condition = TextMentionTermination("TERMINATE")

    # Custom team coordinator selector prompt with priority rules
    selector_prompt = (
        "You are an intelligent team coordinator responsible for selecting "
        "the most appropriate specialist agent to handle the current task "
        "efficiently. Analyze the user's request and conversation context "
        "to determine which agent can best accomplish the objective.\n\n"
        "## Available Specialist Agents:\n"
        "{roles}\n\n"
        "## Selection Strategy:\n\n"
        "**PRIORITY RULE**: ALWAYS select the task_organizer_assistant first to establish "
        "a TODO list and plan the work.\n\n"
        "**Task-Based Selection**:\n"
        "- **Repository analysis, semantic search, code understanding, "
        "initial exploration AFTER planning**: → repository_specialist\n"
        "- **TODO list management, task planning, and session termination**: → task_organizer_assistant\n"
        "- **Coding tasks, code analysis, solution validation, file operations, "
        "reading/writing files, directory navigation**: → coding_specialist\n"
        "- **Git operations, version control, commits, branches, merges, "
        "repository status**: → git_assistant\n\n"
        "## Context Analysis:\n"
        "**Conversation History**:\n"
        "{history}\n\n"
        "**Available Candidates**: {participants}\n\n"
        "**Return only the selected agent name from {participants}.**"
    )

    participants = [task_organizer_assistant, coding_specialist_assistant, git_assistant] + repository_specialists

    # Create SelectorGroupChat team with shared for nested team support
    repository_team = SelectorGroupChat(
        name=team_name,
        participants=participants,
        model_client=model_client,
        termination_condition=termination_condition,
        selector_prompt=selector_prompt,
        description=description,
        max_turns=50,
        emit_team_events=True,
    )

    logger.info(
        f"Successfully created Repository Team with coding specialist, git, "
        f"repository_specialist, and conversation coordinator agents for repository: "
        f"{repository_directory}"
    )
    return repository_team
