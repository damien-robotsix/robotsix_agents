"""
GitHub agent implementation using MCP (Model Context Protocol).
"""

import asyncio
import logging
import os
from typing import Optional

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.tools.mcp import McpWorkbench, StdioServerParams
from robotsix_agents.core import get_config_manager, load_agent_config
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


async def create_mcp_workbench(github_token: Optional[str] = None) -> McpWorkbench:
    """
    Create and configure the MCP workbench for GitHub integration.

    Args:
        github_token: Optional GitHub token. If not provided,
                     will try to get from environment.

    Returns:
        McpWorkbench: The configured MCP workbench for GitHub.
    """
    # Get GitHub token from parameter or fallback to environment
    if not github_token:
        github_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN") or os.getenv(
            "GITHUB_TOKEN"
        )

    if not github_token:
        raise ValueError(
            "GitHub token not found. Set github_token in configuration, or "
            "set GITHUB_PERSONAL_ACCESS_TOKEN or GITHUB_TOKEN environment "
            "variable."
        )

    # Configure MCP server parameters for GitHub
    server_params = StdioServerParams(
        command="docker",
        args=[
            "run",
            "-i",
            "--rm",
            "-e",
            "GITHUB_PERSONAL_ACCESS_TOKEN",
            "ghcr.io/github/github-mcp-server",
        ],
        env={
            "GITHUB_PERSONAL_ACCESS_TOKEN": github_token,
        },
        read_timeout_seconds=120,
    )

    logger.info("Initializing GitHub MCP workbench")
    return McpWorkbench(server_params)


async def create_agent() -> AssistantAgent:
    """
    Create a GitHub agent instance.

    This function follows the robotsix_agents pattern and is called by the orchestrator
    to create participant agents.

    Returns:
        Configured GitHub AssistantAgent
    """

    # Get configuration manager
    config_manager = get_config_manager()

    # Load agent-specific configuration
    agent_config = load_agent_config("github")

    # Get model client from configuration manager
    model_client = config_manager.get_model_client("github")

    # Get GitHub token from configuration or environment
    github_token = agent_config.get("github_token")

    # Create MCP workbench
    mcp_workbench = await create_mcp_workbench(github_token)

    # Create assistant agent with GitHub MCP integration
    assistant_agent = AssistantAgent(
        name="github_assistant",
        model_client=model_client,
        workbench=mcp_workbench,
        max_tool_iterations=50,
        description=agent_config.get(
            "description",
            "A GitHub assistant agent that can search into GitHub content on the web ",
        ),
    )

    logger.info("Successfully created GitHub agent")
    return assistant_agent
