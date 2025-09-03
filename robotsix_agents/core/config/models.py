"""
Pydantic models for robotsix-agents configuration management.
"""

from typing import Dict, Any
from pydantic import BaseModel, Field
from autogen_core import ComponentModel


class RobotsixAgentsConfig(BaseModel):
    """Main configuration model for robotsix-agents package."""

    # Default model provider configuration - used as fallback for all agents
    default_model_provider: ComponentModel = Field(
        default=ComponentModel(
            provider="autogen_ext.models.openai.OpenAIChatCompletionClient",
            config={
                "model": "deepseek/deepseek-chat-v3-0324",
                "base_url": "https://openrouter.ai/api/v1",
                "api_key": "<API_KEY>",
                "model_info": {
                    "vision": False,
                    "json_output": True,
                    "structured_output": True,
                    "family": "deepseek",
                    "function_calling": True,
                    "multiple_system_messages": True,
                },
            },
        ),
        description="Default model provider configuration used when agent "
        "doesn't specify one",
    )

    # Agent-specific configurations
    agents: Dict[str, Any] = Field(
        default_factory=dict, description="Agent-specific configurations"
    )
