from autogen_agentchat.agents import AssistantAgent
from autogen_ext.memory.mem0 import Mem0Memory
from robotsix_agents.core import get_config_manager


def create_memory() -> Mem0Memory:
    """
    Create an interaction memory instance.

    Returns:
        Mem0Memory: The created memory instance.
    """
    # Get configuration manager
    config_manager = get_config_manager()

    # Get memory configuration and create Mem0Memory instance if configured
    memory_config = config_manager.get_memory_config("interaction_memory")
    if memory_config:
        # pylint: disable=protected-access
        return Mem0Memory._from_config(  # pyright: ignore[reportPrivateUsage]
            memory_config
        )
    raise ValueError("No memory configuration found for 'interaction_memory'")


def create_agent() -> AssistantAgent:
    """
    Create an assistant agent with interaction memory capabilities.

    Returns:
        AssistantAgent: The configured assistant agent with memory if configured.
    """
    # Get configuration manager
    config_manager = get_config_manager()

    # Get model client from configuration manager
    model_client = config_manager.get_model_client("interaction_memory")

    memory_list = [create_memory()]

    # Create assistant agent (with memory if configured)
    assistant_agent = AssistantAgent(
        max_tool_iterations=5,
        name="interaction_memory",
        description="Agent that remembers past interactions.",
        model_client=model_client,
        memory=memory_list,
    )

    return assistant_agent
