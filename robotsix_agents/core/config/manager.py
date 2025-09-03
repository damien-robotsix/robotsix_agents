"""
Main configuration manager for robotsix-agents.
"""

from typing import Dict, Any, Optional
from autogen_ext.memory.mem0 import Mem0MemoryConfig
from .models import RobotsixAgentsConfig
from .file_manager import ConfigFileManager
from .client_factory import ModelClientFactory
from .validator import ConfigValidator
from .agent_defaults import AgentDefaultsLoader


class ConfigManager:
    """High-level configuration manager that orchestrates all components."""

    def __init__(self, app_name: str = "robotsix-agents"):
        """
        Initialize the configuration manager.

        Args:
            app_name: Application name for platformdirs
        """
        self.file_manager = ConfigFileManager(app_name)
        self.client_factory = ModelClientFactory()
        self.validator = ConfigValidator()
        self.agent_defaults_loader = AgentDefaultsLoader()

    def get_config_dir(self):
        """Get the configuration directory path."""
        return self.file_manager.get_config_dir()

    def get_config_file(self):
        """Get the configuration file path."""
        return self.file_manager.get_config_file()

    def ensure_config_dir(self) -> None:
        """Create configuration directory if it doesn't exist."""
        self.file_manager.ensure_config_dir()

    def create_default_config(self, force: bool = False) -> None:
        """
        Create a default configuration file.

        Args:
            force: If True, overwrite existing config file
        """
        self.file_manager.create_default_config(force=force)

    def load_config(self) -> RobotsixAgentsConfig:
        """
        Load and validate configuration from file.

        Returns:
            Loaded and validated configuration object
        """
        config = self.file_manager.load_config()
        self.validator.validate_full_config(config)
        return config

    def update_config(self, updates: Dict[str, Any]) -> None:
        """
        Update configuration with new values.

        Args:
            updates: Dictionary of configuration updates
        """
        updated_config = self.file_manager.update_config(updates)
        self.validator.validate_full_config(updated_config)

    def get_model_client(self, agent_name: Optional[str] = None):
        """
        Get configured model client for an agent with fallback to default.

        Args:
            agent_name: Optional agent name for agent-specific model

        Returns:
            Configured model client instance
        """
        config = self.load_config()
        return self.client_factory.get_model_client(config, agent_name)

    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific agent with default fallback.

        Args:
            agent_name: Name of the agent

        Returns:
            Agent-specific configuration dictionary with model client

        The configuration hierarchy is:
        1. Agent package defaults (shipped with code)
        2. Main user config (existing config.yaml)
        """
        # Validate agent name
        if not agent_name or not agent_name.strip():
            raise ValueError("Agent name must be a non-empty string")

        # Start with agent defaults (package defaults only)
        merged_config = self.agent_defaults_loader.load_agent_default(agent_name)

        # Load main user config
        config = self.load_config()

        # Merge with user-specific config from main config file
        agents_dict: Dict[str, Any] = config.agents if config.agents else {}
        user_agent_config = agents_dict.get(agent_name, {})

        # Merge user config on top of defaults
        if user_agent_config:
            merged_config.update(user_agent_config)

        # Validate merged config if it exists
        if merged_config:
            self.validator.validate_agent_config(agent_name, merged_config)

        # Add model client (with fallback logic)
        merged_config["model_client"] = self.get_model_client(agent_name)

        return merged_config

    def get_memory_config(
        self, agent_name: Optional[str] = None
    ) -> Optional[Mem0MemoryConfig]:
        """
        Get memory configuration for an agent.

        Args:
            agent_name: Optional agent name for agent-specific memory config

        Returns:
            Memory configuration instance or None if agent has no memory config

        This method checks agent defaults first, then user configuration.
        """
        if not agent_name:
            return None

        # Get full agent configuration (includes defaults + user config)
        agent_config = self.get_agent_config(agent_name)

        # Look for memory config in agent configuration
        if "memory" in agent_config:
            memory_config_dict = agent_config["memory"]
            if isinstance(memory_config_dict, dict):
                return Mem0MemoryConfig.model_validate(memory_config_dict)
            if isinstance(memory_config_dict, Mem0MemoryConfig):
                return memory_config_dict

        # Return None if no memory configuration is specified
        return None
