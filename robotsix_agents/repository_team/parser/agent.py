"""
Repository Parser agent implementation.

This module provides a Repository Parser agent that uses tools to index
and search repository content using Qdrant vector store.
"""

import logging
from autogen_agentchat.agents import AssistantAgent
from robotsix_agents.core import get_config_manager, load_agent_config
from .tools import RepositoryParser

logger = logging.getLogger(__name__)


async def create_agent(repository_directory: str) -> AssistantAgent:
    """
    Create a Repository Parser agent instance.

    This function follows the robotsix_agents pattern and is called by the orchestrator
    to create participant agents.

    Args:
        repository_directory: Repository directory path to parse

    Returns:
        Configured Repository Parser AssistantAgent
    """
    # Get configuration manager
    config_manager = get_config_manager()

    # Load agent-specific configuration
    agent_config = load_agent_config("repository_parser")

    # Get model client from configuration manager
    model_client = config_manager.get_model_client("repository_parser")

    # Extract parser configuration from agent config
    parser_config = None
    if agent_config and any(
        key in agent_config for key in ["vector_store", "embedder"]
    ):
        parser_config = {
            "vector_store": agent_config.get("vector_store"),
            "embedder": agent_config.get("embedder"),
        }

    # Initialize the repository parser
    repo_parser = RepositoryParser(repo_path=repository_directory, config=parser_config)

    # Automatically perform indexing at agent creation
    try:
        logger.info(f"Automatically indexing repository: {repository_directory}")
        indexing_result = repo_parser.index_repository()
        logger.info(f"Repository indexing completed: {indexing_result}")
    except Exception as e:
        logger.error(f"Error during automatic indexing: {e}")
        # Continue with agent creation even if indexing fails

    async def search_repository(query: str):
        """Search repository content using semantic search."""
        try:
            results = repo_parser.search_repository(query, 5)
            if not results:
                return "No results found for the query."

            response = f"Found {len(results)} results for '{query}':\n\n"
            for i, result in enumerate(results, 1):
                response += f"{i}. File: {result['filename']}\n"
                response += f"   Score: {result['score']:.3f}\n"
                response += f"   Content: {result['text'][:200]}...\n\n"

            return response
        except Exception as e:
            logger.error(f"Error searching repository: {e}")
            return f"Error searching repository: {str(e)}"

    # Create tools list for the agent (only search functionality)
    tool_functions = [
        search_repository,
    ]

    # Create assistant agent with Repository Parser integration
    assistant_agent = AssistantAgent(
        name="repository_parser",
        model_client=model_client,
        tools=tool_functions,
        max_tool_iterations=50,
        system_message=agent_config.get(
            "system_message",
            (
                "You are a proficient semantic parser with the ability to search "
                "the repository for context relevant to a given task. Your primary "
                "role is to provide a comprehensive summary based on the search "
                "results, assisting the team in understanding the codebase. You do "
                "not solve tasks directly but rather equip the team with the necessary "
                "information to do so. Your focus is on interpreting the query, "
                "finding relevant information, and presenting it clearly. You do not terminate the conversation."
            ),
        ),
        description=agent_config.get(
            "description",
            f"A Repository Parser assistant agent powered by CocoIndex. Provides "
            f"semantic search capabilities across repository content using PostgreSQL "
            f"vector store. Repository is automatically indexed on startup. "
            f"Working on repository: {repository_directory}",
        ),
    )

    logger.info(
        f"Successfully created Repository Parser agent for repository: "
        f"{repository_directory}"
    )
    return assistant_agent
