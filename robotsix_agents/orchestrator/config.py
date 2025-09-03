"""
Configuration models for the orchestrator agent.
"""

from typing import List, Optional
from pydantic import BaseModel, Field

from autogen_core import ComponentModel


class OrchestratorConfig(BaseModel):
    """Configuration for the orchestrator agent."""

    name: str = Field(default="orchestrator", description="Name of the orchestrator")
    description: str = Field(
        default="Multi-agent orchestrator using SelectorGroupChat",
        description="Description of the orchestrator",
    )

    # SelectorGroupChat configuration
    max_turns: Optional[int] = Field(
        default=50, description="Maximum number of conversation turns"
    )

    # Participant configuration
    participants: List[str] = Field(description="List of participant agent names")

    # User proxy configuration
    enable_user_proxy: bool = Field(
        default=False, description="Enable UserProxyAgent for human interaction"
    )

    # Model provider for the orchestrator itself
    model_provider: Optional[ComponentModel] = Field(
        default=None,
        description="Model provider for the orchestrator "
        "(optional, uses default if not specified)",
    )
