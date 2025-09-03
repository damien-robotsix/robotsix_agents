"""
Git agent module for robotsix_agents.

This module provides a Git agent that uses a Docker-based git MCP server
to interact with local Git repositories.
"""

from .agent import create_agent

__all__ = ["create_agent"]
