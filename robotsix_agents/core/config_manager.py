"""
Centralized configuration management for robotsix-agents package.

This module provides unified configuration management using platformdirs
to store configuration files in the appropriate user directory.
Follows AutoGen's provider pattern for model configuration.
"""

import argparse
import logging
import sys
from functools import lru_cache
from typing import Dict, Any
from .config import ConfigManager, RobotsixAgentsConfig
from .config.exceptions import ConfigError

# Export the main classes so they can be imported from this module
__all__ = [
    'ConfigManager',
    'RobotsixAgentsConfig',
    'get_config_manager',
    'get_config',
    'load_agent_config',
    'init_config'
]


@lru_cache(maxsize=1)
def get_config_manager() -> ConfigManager:
    """
    Get the global configuration manager instance.

    Returns:
        ConfigManager instance
    """
    return ConfigManager()


def init_config(force: bool = False) -> None:
    """Initialize configuration for robotsix-agents package.

    Args:
        force: If True, overwrite existing config file
    """
    manager = get_config_manager()
    manager.create_default_config(force=force)


def get_config() -> RobotsixAgentsConfig:
    """
    Get the global configuration.

    Returns:
        Global configuration object
    """
    manager = get_config_manager()
    return manager.load_config()


def load_agent_config(agent_name: str) -> Dict[str, Any]:
    """
    Load configuration for a specific agent.

    Args:
        agent_name: Name of the agent

    Returns:
        Agent configuration dictionary
    """
    manager = get_config_manager()
    return manager.get_agent_config(agent_name)


def main():
    """Main entry point for console script."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    logger = logging.getLogger(__name__)

    # Setup argument parser
    parser = argparse.ArgumentParser(
        prog='robotsix-agents-config',
        description='Configure robotsix-agents package'
    )

    subparsers = parser.add_subparsers(
        dest='command', help='Available commands'
    )

    # Init command
    init_parser = subparsers.add_parser(
        'init', help='Initialize configuration'
    )
    init_parser.add_argument(
        '--force',
        action='store_true',
        help='Overwrite existing configuration file'
    )

    # Parse arguments
    args = parser.parse_args()

    if args.command == 'init':
        try:
            init_config(force=args.force)
            logger.info("Configuration initialization completed successfully")
        except ConfigError as e:
            logger.error("Configuration error: %s", e)
            return 1
        except OSError as e:
            logger.error("File system error during config init: %s", e)
            return 1
    else:
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
if __name__ == "__main__":
    sys.exit(main())
