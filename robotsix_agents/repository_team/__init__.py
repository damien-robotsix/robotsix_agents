"""
Repository Team module.

This module provides a team of agents (coding specialist and git) that work
together to handle repository operations using SelectorGroupChat.
"""

from .agent import create_agent

__all__ = ["create_agent"]