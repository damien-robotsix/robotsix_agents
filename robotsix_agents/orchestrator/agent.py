"""
Orchestrator agent implementation using SelectorGroupChat.
"""

import asyncio
import importlib
import logging
from typing import AsyncGenerator, List, Optional, Union

from autogen_agentchat.agents import UserProxyAgent
from autogen_agentchat.base import ChatAgent, TaskResult, Team
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.messages import (
    BaseAgentEvent,
    BaseChatMessage,
    TextMessage,
)
from autogen_agentchat.teams import SelectorGroupChat
from autogen_core import CancellationToken
from autogen_core.memory import MemoryContent
from autogen_core.models import ChatCompletionClient

from ..core.config_manager import ConfigManager, get_config_manager
from ..interaction_memory.agent import create_memory
from .config import OrchestratorConfig

logger = logging.getLogger(__name__)


async def console_input_func(
    prompt: str, cancellation_token: Optional[CancellationToken] = None
) -> str:
    """
    Enhanced console input function for UserProxyAgent that provides context.

    Args:
        prompt: The prompt to display to the user
        cancellation_token: Optional cancellation token

    Returns:
        User input string
    """
    try:
        # Use asyncio.to_thread to avoid blocking the event loop
        user_input = await asyncio.to_thread(input, prompt)
        return user_input.strip()
    except KeyboardInterrupt:
        return "BYE"


class OrchestratorAgent:
    """
    An orchestrator agent that manages multiple participants using SelectorGroupChat.

    This agent creates and coordinates multiple participant agents in a conversation,
    using the SelectorGroupChat for multi-agent collaboration with model-based
    speaker selection.
    """

    def __init__(
        self, config: OrchestratorConfig, config_manager: Optional[ConfigManager] = None
    ):
        """
        Initialize the orchestrator agent.

        Args:
            config: Orchestrator configuration
            config_manager: Optional config manager (uses default if not provided)
        """
        self.config = config
        self.config_manager = config_manager or get_config_manager()

        # Create model client for the orchestrator
        self.model_client = self._create_model_client()

    def _create_model_client(self) -> ChatCompletionClient:
        """Create model client for the orchestrator."""
        if self.config.model_provider:
            # Use orchestrator-specific model provider
            return self.config_manager.client_factory.create_client(
                self.config.model_provider
            )
        else:
            # Use default model provider
            return self.config_manager.get_model_client()

    async def _create_participants(self) -> List[Union[ChatAgent, Team]]:
        """Create participant agents based on configuration."""
        participants: List[Union[ChatAgent, Team]] = []

        for participant_spec in self.config.participants:
            # Parse participant specification (e.g., "git[/path/to/repo]")
            agent_name, params = self._parse_participant_spec(participant_spec)

            # Create participant from module's create_agent() function
            participant = await self._create_participant_from_module(agent_name, params)
            participants.append(participant)

        # Add UserProxyAgent if enabled
        if self.config.enable_user_proxy:
            user_proxy = UserProxyAgent(
                name="user_proxy", input_func=console_input_func
            )
            participants.append(user_proxy)
            logger.info("Added UserProxyAgent to participants")

        logger.info(
            "Created %d participants for orchestrator '%s'",
            len(participants),
            self.config.name,
        )
        return participants

    def _parse_participant_spec(self, participant_spec: str) -> tuple[str, List[str]]:
        """
        Parse participant specification to extract agent name and parameters.

        Supports formats:
        - "agent_name" -> returns ("agent_name", [])
        - "agent_name[param1,param2,param3]" -> returns ("agent_name",
          ["param1", "param2", "param3"])

        Args:
            participant_spec: Participant specification string

        Returns:
            Tuple of (agent_name, parameters_list)
        """
        import re

        # Match pattern: agent_name[parameters]
        pattern = r"^([^[\]]+)(?:\[([^\]]+)\])?$"
        match = re.match(pattern, participant_spec.strip())
        if not match:
            raise ValueError(f"Invalid participant specification: {participant_spec}")

        agent_name = match.group(1)
        params_str = match.group(2)

        params = []
        if params_str:
            # Split comma-separated parameters into a list
            params = [param.strip() for param in params_str.split(",")]

        return agent_name, params

    async def _create_participant_from_module(
        self, agent_name: str, params: Optional[List[str]] = None
    ) -> ChatAgent:
        """Create a participant agent from its module's create_agent() function."""
        if params is None:
            params = []
        try:
            # Import the agent module dynamically
            module_path = f"robotsix_agents.{agent_name}.agent"
            agent_module = importlib.import_module(module_path)

            if hasattr(agent_module, "create_agent"):
                create_agent_func = agent_module.create_agent

                if params:
                    # Check if create_agent_func is async
                    if asyncio.iscoroutinefunction(create_agent_func):
                        participant = await create_agent_func(*params)
                    else:
                        participant = create_agent_func(*params)
                    logger.info(
                        "Created participant '%s' with params: %s",
                        agent_name,
                        params,
                    )
                else:
                    # Check if create_agent_func is async
                    if asyncio.iscoroutinefunction(create_agent_func):
                        participant = await create_agent_func()
                    else:
                        participant = create_agent_func()
                    logger.info(
                        "Created participant '%s'",
                        agent_name,
                    )

                return participant
            else:
                raise AttributeError(
                    f"Module {module_path} does not have create_agent() function"
                )

        except ImportError as e:
            logger.error("Failed to import agent module '%s': %s", agent_name, e)
            raise
        except Exception as e:
            logger.error("Failed to create agent '%s': %s", agent_name, e)
            raise

    def _get_interaction_memory_agent(
        self, participants: List[Union[ChatAgent, Team]]
    ) -> Optional[Union[ChatAgent, Team]]:
        """Get the interaction_memory agent from participants."""
        for participant in participants:
            if participant.name == "interaction_memory":
                return participant
        return None

    async def _save_to_interaction_memory(
        self, task_result: TaskResult, participants: List[Union[ChatAgent, Team]]
    ) -> None:
        """Save task messages to interaction memory agent."""
        interaction_memory_agent = self._get_interaction_memory_agent(participants)
        if not interaction_memory_agent:
            logger.warning("No interaction_memory agent found in participants")
            return

        # Convert task messages to a conversation summary for memory storage
        messages_content: List[str] = []
        for message in task_result.messages:
            if isinstance(message, BaseChatMessage):
                # Format: "Agent: message content"
                source = getattr(message, "source", "unknown")
                content = getattr(message, "content", str(message))
                formatted_msg = f"{source}: {content}"
                messages_content.append(formatted_msg)

        # Create a summary of the conversation
        if messages_content:
            conversation_summary = "\n".join(messages_content)
            memory_content = MemoryContent(
                content=f"Conversation summary:\n{conversation_summary}",
                mime_type="text/plain",
                metadata={
                    "source": "orchestrator",
                    "stop_reason": task_result.stop_reason,
                },
            )

            print("Saving conversation summary to interaction memory...")

            await create_memory().add(memory_content)

    def _create_team(
        self, participants: List[Union[ChatAgent, Team]]
    ) -> SelectorGroupChat:
        """Create the SelectorGroupChat team with shared runtime."""
        # Create termination conditions
        if self.config.enable_user_proxy:
            # When user proxy is enabled, terminate on "BYE" from user
            termination_condition = TextMentionTermination(
                "BYE", sources=["user_proxy"]
            )
        else:
            # When user proxy is disabled, terminate on "TERMINATE" from any agent
            # This allows agents to naturally conclude conversations
            termination_condition = TextMentionTermination("TERMINATE")

        # Create the team with shared runtime to support nested teams properly
        team = SelectorGroupChat(
            participants=participants,
            model_client=self.model_client,
            max_turns=self.config.max_turns,
            termination_condition=termination_condition,
            emit_team_events=True
        )

        return team

    async def run(
        self, task: str
    ) -> AsyncGenerator[Union[BaseAgentEvent, BaseChatMessage, TaskResult], None]:
        """
        Run a task with the orchestrator team and stream events in real-time.

        This method provides real-time visibility into agent selection and interactions
        during the orchestration process.

        Args:
            task: The task description to execute

        Yields:
            BaseAgentEvent: Events like SelectSpeakerEvent showing agent selection
            BaseChatMessage: Messages from agents during execution
            TaskResult: The final result (last item in the stream)
        """
        logger.info("Starting orchestrator task: %s", task)

        participants = await self._create_participants()
        team = self._create_team(participants)

        try:
            async for event in team.run_stream(task=task):
                if isinstance(event, TaskResult):
                    logger.info("Orchestrator task completed")
                    # Add message history to interaction memory agent
                    await self._save_to_interaction_memory(event, participants)
                    yield event
                else:
                    # Other events (messages, etc.)
                    yield event

        except KeyboardInterrupt:
            logger.info("Task interrupted by user")
            # Create a simple TaskResult for interruption
            yield TaskResult(
                messages=[
                    TextMessage(
                        content="Task was interrupted by user.", source="system"
                    )
                ],
                stop_reason="User interruption",
            )

    def get_config(self) -> OrchestratorConfig:
        """Get the orchestrator configuration."""
        return self.config


def create_orchestrator_agent(
    config: OrchestratorConfig, config_manager: Optional[ConfigManager] = None
) -> OrchestratorAgent:
    """
    Create an orchestrator agent from configuration.

    Args:
        config: Orchestrator configuration
        config_manager: Optional config manager

    Returns:
        Configured OrchestratorAgent instance
    """
    return OrchestratorAgent(config=config, config_manager=config_manager)
