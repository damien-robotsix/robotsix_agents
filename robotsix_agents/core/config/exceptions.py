"""
Custom exceptions for robotsix-agents configuration management.
"""


class ConfigError(Exception):
    """Base configuration error."""


class ConfigFileNotFoundError(ConfigError):
    """Configuration file not found."""


class ConfigValidationError(ConfigError):
    """Configuration validation failed."""


class ModelProviderError(ConfigError):
    """Model provider configuration error."""


class ConfigParsingError(ConfigError):
    """Configuration file parsing error."""


class DependencyMissingError(ConfigError):
    """Required dependency is missing."""
