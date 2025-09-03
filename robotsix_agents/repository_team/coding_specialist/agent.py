"""
Coding Specialist agent implementation using MCP (Model Context Protocol).

This module provides a Coding Specialist agent that combines filesystem R/W capabilities
with advanced coding expertise and solution validation before implementation.
"""

import logging
from typing import Dict, Optional

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.tools.mcp import McpWorkbench, StdioServerParams
from robotsix_agents.core import get_config_manager, load_agent_config

logger = logging.getLogger(__name__)


async def create_mcp_workbench(
    working_directory: Optional[str] = None,
) -> McpWorkbench:
    """
    Create and configure the MCP workbench for Coding Specialist integration.

    Args:
        working_directory: The directory the coding specialist agent will work in.
                          If None, will use the current working directory.

    Returns:
        McpWorkbench: The configured MCP workbench for Filesystem operations.
    """
    # Configure MCP server parameters for Coding Specialist
    env_vars: Dict[str, str] = {}
    import os

    # Default to current working directory if no directory specified
    if working_directory is None:
        working_directory = "."

    # Convert relative path to absolute path
    abs_directory = os.path.abspath(working_directory)

    # Configure Docker mount arguments for filesystem access
    docker_args = ["run", "-i", "--rm"]

    # Mount the working directory to /projects/{basename}
    mount_target = f"/projects/{os.path.basename(abs_directory)}"
    docker_args.extend(["--mount", f"type=bind,src={abs_directory},dst={mount_target}"])

    # Add the filesystem server image and entry point
    docker_args.extend(["mcp/filesystem", "/projects"])

    # Configure MCP server parameters for Docker-based filesystem MCP server
    logger.info("Using Docker to run mcp/filesystem server for coding specialist")
    server_params = StdioServerParams(command="docker", args=docker_args, env=env_vars)

    logger.info(
        f"Initializing Coding Specialist MCP workbench with working directory: "
        f"{abs_directory} mounted at {mount_target}"
    )
    return McpWorkbench(server_params)


async def create_agent(
    working_directory: Optional[str] = None,
) -> AssistantAgent:
    """
    Create a Coding Specialist agent instance.

    This function follows the robotsix_agents pattern and is called by the orchestrator
    to create participant agents.

    Args:
        working_directory: The directory the coding specialist agent will work in.
                          If None, will use the current working directory.

    Returns:
        Configured Coding Specialist AssistantAgent
    """
    # Get configuration manager
    config_manager = get_config_manager()

    # Load agent-specific configuration
    agent_config = load_agent_config("coding_specialist")

    # Get model client from configuration manager
    model_client = config_manager.get_model_client("coding_specialist")

    # Default to current working directory if no directory specified
    if working_directory is None:
        working_directory = "."

    mcp_workbench = await create_mcp_workbench(working_directory)

    # Get absolute path and mount target for description
    import os

    abs_working_directory = os.path.abspath(working_directory)
    mount_target = f"/projects/{os.path.basename(abs_working_directory)}"

    # Create assistant agent with Coding Specialist capabilities
    max_tool_iterations = agent_config.get("max_tool_iterations", 75)
    
    assistant_agent = AssistantAgent(
        name="coding_specialist",
        model_client=model_client,
        workbench=mcp_workbench,
        max_tool_iterations=max_tool_iterations,
        system_message=agent_config.get(
            "system_message",
            f"You are an expert Coding Specialist with comprehensive filesystem "
            f"R/W capabilities. Your expertise spans multiple programming languages, "
            f"frameworks, and best practices. You follow instructions from the team coordinator and you do not terminate the conversation.",
        ),
        description=agent_config.get(
            "description",
            f"A Coding Specialist agent with filesystem R/W capabilities that "
            f"validates solutions before implementation. Expert in multiple "
            f"programming languages, frameworks, and software engineering "
            f"best practices. Working directory: {abs_working_directory}",
        ),
    )

    logger.info(
        f"Successfully created Coding Specialist agent for directory: "
        f"{abs_working_directory}"
    )
    return assistant_agent
