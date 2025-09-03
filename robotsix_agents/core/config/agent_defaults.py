"""
Agent-specific default configuration loader for robotsix-agents.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

from .exceptions import ConfigParsingError

logger = logging.getLogger(__name__)


class AgentDefaultsLoader:
    """Loads and manages agent-specific default configurations."""

    def __init__(self, package_name: str = "robotsix_agents"):
        """
        Initialize the agent defaults loader.

        Args:
            package_name: Package name for loading built-in defaults
        """
        self.package_name = package_name

    def get_package_defaults_dir(self) -> Optional[Path]:
        """
        Get the package defaults directory path.

        Returns:
            Path to package defaults directory, or None if not found
        """
        # Try relative to this file first
        current_dir = Path(__file__).parent
        defaults_dir = current_dir.parent.parent / "agent_defaults"
        if defaults_dir.exists():
            return defaults_dir

        # Try installed package location
        try:
            import importlib.util

            spec = importlib.util.find_spec(self.package_name)
            if spec and spec.origin:
                package_dir = Path(spec.origin).parent
                defaults_dir = package_dir / "agent_defaults"
                if defaults_dir.exists():
                    return defaults_dir
        except (ImportError, AttributeError):
            pass

        return None

    def load_agent_default(self, agent_name: str) -> Dict[str, Any]:
        """
        Load default configuration for a specific agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Package default configuration dictionary

        Only loads package defaults - user overrides are handled in main config.yaml
        """
        # Load package defaults only
        package_defaults = self._load_package_default(agent_name)
        if package_defaults:
            logger.debug("Loaded package defaults for agent '%s'", agent_name)
            return package_defaults

        return {}

    def _load_package_default(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        Load package default configuration for an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Package default configuration or None
        """
        defaults_dir = self.get_package_defaults_dir()
        if not defaults_dir:
            logger.debug("No package defaults directory found")
            return None

        config_file = defaults_dir / f"{agent_name}.yaml"
        return self._load_yaml_file(config_file, "package")

    def _load_yaml_file(
        self, config_file: Path, source_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Load YAML configuration from a file.

        Args:
            config_file: Path to the configuration file
            source_type: Type of source ("package" or "user") for logging

        Returns:
            Configuration dictionary or None if file doesn't exist
        """
        if not config_file.exists():
            logger.debug(
                "%s default config file not found: %s", source_type.title(), config_file
            )
            return None

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data is None:
                    return {}
                if not isinstance(data, dict):
                    raise ConfigParsingError(
                        f"{source_type.title()} agent default must be a YAML "
                        f"dictionary, got {type(data).__name__} in {config_file}"
                    )
                logger.debug(
                    "Loaded %s agent defaults from: %s", source_type, config_file
                )
                return data

        except yaml.YAMLError as e:
            raise ConfigParsingError(
                f"Invalid YAML in {source_type} agent default file {config_file}: {e}"
            ) from e
        except (OSError, IOError) as e:
            raise ConfigParsingError(
                f"Error loading {source_type} agent default {config_file}: {e}"
            ) from e

    def list_available_defaults(self) -> Dict[str, bool]:
        """
        List all available package agent defaults.

        Returns:
            Dictionary mapping agent names to availability:
            {"agent_name": True/False}
        """
        agents = {}

        # Check package defaults
        package_defaults_dir = self.get_package_defaults_dir()
        if package_defaults_dir:
            for config_file in package_defaults_dir.glob("*.yaml"):
                agent_name = config_file.stem
                agents[agent_name] = True

        return agents
