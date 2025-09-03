"""
Model client factory for robotsix-agents configuration.
"""

import logging
from typing import Optional

from autogen_core.models import ChatCompletionClient
from autogen_core import ComponentModel

from .models import RobotsixAgentsConfig
from .exceptions import ModelProviderError

logger = logging.getLogger(__name__)


class ModelClientFactory:
    """Factory for creating model clients."""

    def create_client(self, provider_config: ComponentModel) -> ChatCompletionClient:
        """
        Create a model client from provider configuration.

        Args:
            provider_config: Provider configuration

        Returns:
            Configured model client instance

        Raises:
            ModelProviderError: If client creation fails
        """
        try:
            client_class = ChatCompletionClient
            config_dict = provider_config.model_dump()
            return client_class.load_component(config_dict)
        except (ImportError, AttributeError, ValueError, TypeError) as e:
            raise ModelProviderError(f"Failed to create model client: {e}") from e

    def get_model_client(
        self, config: RobotsixAgentsConfig, agent_name: Optional[str] = None
    ) -> ChatCompletionClient:
        """
        Get configured model client for an agent with fallback to default.

        Args:
            config: Main configuration object
            agent_name: Optional agent name for agent-specific model

        Returns:
            Configured model client instance

        Behavior:
            1. If agent_name is provided and agent has model_provider:
               use agent's provider
            2. Otherwise: use default_model_provider
        """
        # Try to get agent-specific model provider first
        agent_has_provider = agent_name and config.agents.get(agent_name, {}).get(
            "model_provider"
        )

        if agent_has_provider and agent_name:
            provider_config_dict = config.agents[agent_name]["model_provider"]
            provider_config = ComponentModel(**provider_config_dict)
            logger.info("Using agent-specific model provider for '%s'", agent_name)
        else:
            # Fallback to default model provider
            provider_config = config.default_model_provider
            if agent_name:
                logger.info(
                    "Agent '%s' has no specific model provider, using default",
                    agent_name,
                )
            else:
                logger.info("Using default model provider")

        # Create and return the model client
        return self.create_client(provider_config)
