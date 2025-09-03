"""
Configuration validator for robotsix-agents.

This module implements a hybrid validation approach that combines:
1. AutoGen's built-in Pydantic schema validation (for type checking and
   structure)
2. Domain-specific business logic validation (for robotsix-agents requirements)

This ensures both compatibility with AutoGen and enforcement of robotsix-agents
specific configuration requirements.
"""

from typing import Dict, Any
import importlib
from autogen_core import ComponentModel
from .models import RobotsixAgentsConfig
from .exceptions import ConfigValidationError


class ConfigValidator:
    """
    Validates configuration using a hybrid approach.

    This validator leverages AutoGen's built-in Pydantic validation for basic
    schema validation, then adds robotsix-agents specific business logic
    validation on top. This approach ensures:
    - Compatibility with AutoGen's validation expectations
    - Enforcement of robotsix-agents specific requirements
    - Early detection of configuration issues
    """

    def validate_provider_config(self, config: ComponentModel) -> None:
        """
        Validate provider configuration beyond AutoGen's basic validation.

        This method performs robotsix-agents specific provider validation that
        AutoGen doesn't provide, such as checking if custom provider classes
        are actually importable and are valid classes.

        Args:
            config: Provider configuration to validate

        Raises:
            ConfigValidationError: If validation fails
        """
        # Check if provider class exists and is importable
        module_path = None
        class_name = None
        try:
            module_path, class_name = config.provider.rsplit(".", 1)
            module = importlib.import_module(module_path)
            provider_class = getattr(module, class_name)

            # Basic sanity check - ensure it's a class
            if not isinstance(provider_class, type):
                raise ConfigValidationError(
                    f"Provider '{config.provider}' is not a class"
                )

        except ImportError as e:
            raise ConfigValidationError(
                f"Cannot import provider module '{module_path}': {e}"
            ) from e
        except AttributeError as exc:
            error_msg = (
                f"Provider class '{class_name}' not found in " f"module '{module_path}'"
            )
            raise ConfigValidationError(error_msg) from exc
        except ValueError as exc:
            raise ConfigValidationError(
                (
                    f"Invalid provider format '{config.provider}'. "
                    "Expected 'module.path.ClassName'"
                )
            ) from exc
        except TypeError as e:
            raise ConfigValidationError(
                f"Error validating provider '{config.provider}': {e}"
            ) from e

    def validate_agent_config(self, agent_name: str, config: Dict[str, Any]) -> None:
        """
        Validate agent-specific configuration.

        Args:
            agent_name: Name of the agent
            config: Agent configuration dictionary

        Raises:
            ConfigValidationError: If validation fails
        """
        # Validate agent name
        if not agent_name.strip():
            error_msg = "Agent name cannot be empty or whitespace"
            raise ConfigValidationError(error_msg)

        # If agent has model_provider, validate it
        if "model_provider" in config:
            try:
                provider_config = ComponentModel(**config["model_provider"])
                self.validate_provider_config(provider_config)
            except (ValueError, TypeError, KeyError) as e:
                error_msg = f"Invalid model provider for agent '{agent_name}': {e}"
                raise ConfigValidationError(error_msg) from e

    def validate_full_config(self, config: RobotsixAgentsConfig) -> None:
        """
        Validate the complete configuration.

        Args:
            config: Complete configuration to validate

        Raises:
            ConfigValidationError: If validation fails
        """
        # Validate default model provider
        try:
            self.validate_provider_config(config.default_model_provider)
        except (ValueError, TypeError, AttributeError) as e:
            raise ConfigValidationError(f"Invalid default model provider: {e}") from e

        # Validate each agent configuration
        if config.agents:
            for agent_name, agent_config in config.agents.items():
                try:
                    self.validate_agent_config(agent_name, agent_config)
                except (ValueError, TypeError, KeyError) as e:
                    raise ConfigValidationError(
                        f"Invalid configuration for agent '{agent_name}': {e}"
                    ) from e

    def validate_config_dict(self, config_dict: Dict[str, Any]) -> None:
        """
        Validate configuration dictionary using hybrid approach.

        This method implements the hybrid validation strategy:
        1. First, leverage AutoGen's Pydantic validation by creating the
           RobotsixAgentsConfig object (validates types and structure)
        2. Then, apply robotsix-agents specific business logic validation

        Args:
            config_dict: Configuration dictionary

        Raises:
            ConfigValidationError: If validation fails
        """
        try:
            # Step 1: AutoGen's built-in Pydantic validation
            # This validates types, structure, and AutoGen requirements
            config = RobotsixAgentsConfig(**config_dict)

            # Step 2: robotsix-agents specific business logic validation
            # This adds domain-specific validation beyond AutoGen's scope
            self.validate_full_config(config)

        except (ValueError, TypeError, KeyError) as e:
            error_msg = f"Configuration validation failed: {e}"
            raise ConfigValidationError(error_msg) from e
