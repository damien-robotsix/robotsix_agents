# AutoGen-Style Provider Configuration for Robotsix Agents

This document describes the AutoGen-compatible provider configuration system for robotsix-agents.

## Overview

The configuration system follows AutoGen's provider pattern, allowing you to specify different model providers (OpenAI, Anthropic, Azure OpenAI, Ollama, etc.) in a YAML configuration file. Each agent can have its own provider configuration, with fallback to a default provider.

## Configuration Structure

```yaml
# Default model provider used by all agents unless they specify their own
default_model_provider:
  provider: <fully_qualified_provider_class_name>
  config:
    <provider_specific_parameters>

# Agent-specific configurations
agents:
  agent_name:
    # Optional: Override the default model provider
    model_provider:
      provider: <provider_class_name>
      config:
        <provider_specific_parameters>

    # Custom agent settings
    custom_instructions: "Agent-specific instructions"
    other_setting: "value"
```

## Available Providers

Robotsix agents supports all AutoGen-compatible model providers. For the complete list of available providers and their configuration options, please refer to the [AutoGen Models documentation](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/models.html).

## Usage

```bash
ra-config init
```

This creates a default configuration file at `~/.config/robotsix-agents/config.yaml`.

To overwrite an existing configuration file, use the `--force` option:

```bash
ra-config init --force
```
