"""
File operations manager for robotsix-agents configuration.
"""

import logging
from pathlib import Path
from typing import Dict, Any, cast
import platformdirs
import yaml

from .models import RobotsixAgentsConfig
from .exceptions import ConfigFileNotFoundError, ConfigParsingError
from .agent_defaults import AgentDefaultsLoader

logger = logging.getLogger(__name__)


class ConfigFileManager:
    """Manages configuration file operations."""

    def __init__(self, app_name: str = "robotsix-agents"):
        """
        Initialize the file manager.

        Args:
            app_name: Application name for platformdirs
        """
        self.app_name = app_name
        self.config_dir = Path(platformdirs.user_config_dir(app_name))
        self.config_file = self.config_dir / "config.yaml"
        self.agent_defaults_loader = AgentDefaultsLoader()

    def get_config_dir(self) -> Path:
        """
        Get the configuration directory path.

        Returns:
            Path to the configuration directory
        """
        return self.config_dir

    def get_config_file(self) -> Path:
        """
        Get the configuration file path.

        Returns:
            Path to the configuration file
        """
        return self.config_file

    def ensure_config_dir(self) -> None:
        """Create configuration directory if it doesn't exist."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def create_default_config(self, force: bool = False) -> None:
        """
        Create a default configuration file with agent defaults included.

        Args:
            force: If True, overwrite existing config file

        Creates config.yaml with default values and all available agent defaults
        for user customization.
        """
        self.ensure_config_dir()

        if not self.config_file.exists() or force:
            # Start with base default config
            default_config = RobotsixAgentsConfig()

            # Load all available agent defaults
            available_agents = self.agent_defaults_loader.list_available_defaults()
            agents_config = {}

            for agent_name in available_agents:
                agent_defaults = self.agent_defaults_loader.load_agent_default(
                    agent_name
                )
                if agent_defaults:
                    agents_config[agent_name] = agent_defaults
                    logger.debug("Included defaults for agent '%s'", agent_name)

            # Create config with agent defaults included
            config_data = default_config.model_dump()
            if agents_config:
                config_data["agents"] = agents_config
                agent_count = len(agents_config)
                logger.info("Included defaults for %d agents", agent_count)

            # Create and save the comprehensive config
            comprehensive_config = RobotsixAgentsConfig(**config_data)
            self.save_config(comprehensive_config)

            if force:
                logger.info("Overwritten configuration file at: %s", self.config_file)
            else:
                logger.info(
                    "Created default configuration file at: %s", self.config_file
                )
            logger.info("Configuration includes defaults for all available agents.")
            logger.info("Please edit this file to configure your agents.")
        else:
            logger.info("Configuration file already exists at: %s", self.config_file)
            logger.info("Use --force to overwrite the existing configuration.")

    def load_config(self) -> RobotsixAgentsConfig:
        """
        Load configuration from file.

        Returns:
            Loaded configuration object

        Raises:
            ConfigFileNotFoundError: If config file doesn't exist
            ConfigParsingError: If config format is invalid
        """
        if not self.config_file.exists():
            raise ConfigFileNotFoundError(
                f"Configuration file not found: {self.config_file}. "
                "Run 'python -m robotsix_agents.config_manager init'"
            )

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                raw_data = yaml.safe_load(f)

                if raw_data is None:
                    data = {}
                elif not isinstance(raw_data, dict):
                    raise ConfigParsingError(
                        (
                            "Configuration file must contain a YAML dictionary, "
                            f"got {type(raw_data).__name__}"
                        )
                    )
                else:
                    data = cast(Dict[str, Any], raw_data)

                return RobotsixAgentsConfig(**data)

        except yaml.YAMLError as e:
            raise ConfigParsingError(f"Invalid YAML in config file: {e}") from e
        except (OSError, IOError) as e:
            raise ConfigParsingError(f"Error loading configuration: {e}") from e

    def save_config(self, config: RobotsixAgentsConfig) -> None:
        """
        Save configuration to file.

        Args:
            config: Configuration object to save
        """
        self.ensure_config_dir()

        # Convert to dict for YAML serialization
        config_dict = config.model_dump()

        # Write the configuration
        with open(self.config_file, "w", encoding="utf-8") as f:
            yaml.dump(
                config_dict, f, default_flow_style=False, indent=2
            )  # type: ignore

    def update_config(self, updates: Dict[str, Any]) -> RobotsixAgentsConfig:
        """
        Update configuration with new values and save.

        Args:
            updates: Dictionary of configuration updates

        Returns:
            Updated configuration object
        """
        # Load existing config or create default
        try:
            config = self.load_config()
        except ConfigFileNotFoundError:
            self.create_default_config()
            config = self.load_config()

        # Update with new values
        config_dict = config.model_dump()
        config_dict.update(updates)

        # Validate updated config
        updated_config = RobotsixAgentsConfig(**config_dict)

        # Save updated config
        self.save_config(updated_config)

        return updated_config
