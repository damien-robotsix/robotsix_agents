"""
Calendar Agent Module

This module provides functionality to create assistant agents with CalDAV capabilities.
"""

from .agent import create_agent
from .tools import create_calendar_event

__all__ = ["create_agent", "create_calendar_event"]
