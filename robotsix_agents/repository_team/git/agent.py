"""
Git agent implementation using MCP (Model Context Protocol).

This module provides a Git agent that uses a Docker-based git MCP server
to interact with local Git repositories programmatically.
"""

import asyncio
import logging
from typing import Dict

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.tools.mcp import McpWorkbench, StdioServerParams
from robotsix_agents.core import get_config_manager, load_agent_config

logger = logging.getLogger(__name__)


async def create_mcp_workbench() -> McpWorkbench:
    """
    Create and configure the MCP workbench for Git integration.

    Args:
        repository_directory: Working directory for Git operations that will be
                             mounted in Docker container.

    Returns:
        McpWorkbench: The configured MCP workbench for Git operations.
    """
    # Configure MCP server parameters for Git
    # The Docker-based git MCP server doesn't require authentication but can optionally
    # be configured with environment variables for specific behavior
    env_vars: Dict[str, str] = {}

    # Configure MCP server parameters for Docker-based git MCP server
    logger.info("Using Docker to run mcp/git server")
    server_params = StdioServerParams(
        command="python", args=["-m", "mcp_server_git"], env=env_vars
    )

    logger.info("Initializing Git MCP workbench with Docker")
    return McpWorkbench(server_params)


async def create_agent(repository_directory: str) -> AssistantAgent:
    """
    Create a Git agent instance.

    This function follows the robotsix_agents pattern and is called by the orchestrator
    to create participant agents.

    Args:
        repository_directory: Repository directory path.

    Returns:
        Configured Git AssistantAgent
    """

    # Get configuration manager
    config_manager = get_config_manager()

    # Load agent-specific configuration
    agent_config = load_agent_config("git")

    # Get model client from configuration manager
    model_client = config_manager.get_model_client("git")
    mcp_workbench = await create_mcp_workbench()

    # Create assistant agent with Git MCP integration
    assistant_agent = AssistantAgent(
        name="git_assistant",
        model_client=model_client,
        workbench=mcp_workbench,
        max_tool_iterations=20,
        system_message=agent_config.get(
            "system_message",
            "You are a helpful Git assistant that can interact with local Git "
            "repositories. You can perform various Git operations including "
            "status checks, branching, staging, committing, pushing, pulling, "
            "diffing, logging, and more. Always be precise and careful with "
            "Git operations, especially destructive ones. Ask for confirmation "
            "before performing potentially dangerous operations like "
            "git reset --hard or git clean -f."
            f"The repository is placed in {repository_directory}."
            "You follow instructions from the team coordinator and you do not terminate the conversation.",
        ),
        description=agent_config.get(
            "description",
            f"A Git assistant agent that can perform comprehensive Git operations "
            f"on local repositories using a Docker-based git MCP server. "
            f"Working on repository: {repository_directory}",
        ),
    )

    logger.info("Successfully created Git agent")
    return assistant_agent
