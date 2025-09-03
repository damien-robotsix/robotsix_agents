"""
CLI interface for the robotsix agents orchestrator functionality.
"""

import argparse
import asyncio
import logging
import sys

from autogen_agentchat.base import TaskResult, Response
from autogen_agentchat.messages import (
    SelectSpeakerEvent,
    TextMessage,
    ToolCallExecutionEvent,
    ToolCallRequestEvent,
)

from .agent import OrchestratorAgent
from .config import OrchestratorConfig
from ..core.config_manager import get_config_manager
from ..core.config.exceptions import (
    ConfigError,
    ModelProviderError,
    DependencyMissingError,
)


def create_orchestrator_agent_from_config(
    agent_name: str = "orchestrator", enable_user_proxy: bool = False
) -> OrchestratorAgent:
    """
    Create an orchestrator agent from configuration by name.

    Args:
        agent_name: Name for the orchestrator config lookup
        enable_user_proxy: Whether to enable UserProxyAgent for interaction

    Returns:
        Configured OrchestratorAgent instance
    """
    config_manager = get_config_manager()
    orchestrator_config_data = config_manager.get_agent_config(agent_name)
    # Parse the config data into OrchestratorConfig
    orchestrator_config = OrchestratorConfig(**orchestrator_config_data)
    # Override the enable_user_proxy setting if provided
    orchestrator_config.enable_user_proxy = enable_user_proxy
    return OrchestratorAgent(config=orchestrator_config, config_manager=config_manager)


async def run_task_with_streaming(agent: OrchestratorAgent, task: str) -> str:
    """Run a task with real-time agent selection display."""
    print(f"🚀 Orchestrating task: {task}")
    print("=" * 60)

    final_result = ""

    try:
        async for event in agent.run(task):
            if isinstance(event, SelectSpeakerEvent):
                # Show real-time agent selection
                selected_agents = event.content
                if selected_agents:
                    print(f"🤖 Agent selected: {selected_agents[0]}")

            elif isinstance(event, TextMessage):
                # Show agent messages (full content)
                source = event.source
                content = event.content
                print(f"💬 {source}: {content}")

            elif isinstance(event, ToolCallRequestEvent):
                # Show tool call request details
                source = event.source
                tool_calls = event.content
                print(f"🔨 {source}: Tool request")
                for i, tool_call in enumerate(tool_calls):
                    print(f"   Tool {i+1}: {tool_call.name}")
                    if hasattr(tool_call, "arguments") and tool_call.arguments:
                        args_str = str(tool_call.arguments)
                        if len(args_str) > 150:
                            args_str = args_str[:150] + "..."
                        print(f"   Arguments: {args_str}")

            elif isinstance(event, ToolCallExecutionEvent):
                # Show tool call execution details
                source = event.source
                tool_calls = event.content
                print(f"🔧 {source}: Tool execution")
                for i, tool_call in enumerate(tool_calls):
                    print(f"   Tool {i+1}: {tool_call.name}")
                    if hasattr(tool_call, "content") and tool_call.content:
                        # Truncate long content for readability
                        content_str = str(tool_call.content)
                        if len(content_str) > 200:
                            content_str = content_str[:200] + "..."
                        print(f"   Result: {content_str}")

            elif isinstance(event, Response):
                # Show detailed response information
                source = getattr(event.chat_message, "source", "unknown")
                content = getattr(
                    event.chat_message, "content", str(event.chat_message)
                )
                msg_type = type(event.chat_message).__name__
                print(f"📤 {source}: Response ({msg_type})")

                # Show inner messages details
                if hasattr(event, "inner_messages") and event.inner_messages:
                    print(f"   Inner messages: {len(event.inner_messages)}")
                    for j, inner_msg in enumerate(
                        event.inner_messages[:3]
                    ):  # Show first 3
                        inner_type = type(inner_msg).__name__
                        inner_source = getattr(inner_msg, "source", "unknown")
                        print(f"     {j+1}. {inner_type} from {inner_source}")
                    if len(event.inner_messages) > 3:
                        print(f"     ... and {len(event.inner_messages) - 3} more")

                # Show content with more context
                content_str = str(content)
                if len(content_str) > 200:
                    content_str = content_str[:200] + "..."
                print(f"   Content: {content_str}")

                # Show additional response attributes
                if hasattr(event, "chat_message"):
                    chat_msg = event.chat_message
                    if hasattr(chat_msg, "models_usage") and chat_msg.models_usage:
                        print(f"   Model usage: {chat_msg.models_usage}")

            elif isinstance(event, TaskResult):
                # Final result
                print("=" * 60)
                print("✅ Task completed!")
                if event.messages:
                    last_message = event.messages[-1]
                    if isinstance(last_message, TextMessage):
                        final_result = last_message.content
                break

    except KeyboardInterrupt:
        print("\n⚠️ Task interrupted by user.")
        final_result = "Task was interrupted by user."

    return final_result


async def interactive_session(agent: OrchestratorAgent):
    """Run interactive orchestration session using UserProxy agent."""
    print("Robotsix Agents Orchestrator - Interactive Session")
    print(
        "The orchestrator will coordinate with agents and request "
        "your input when needed."
    )

    print("Type 'BYE' to end the session.")
    print("=" * 60)

    try:
        print("\n🚀 Starting interactive orchestrator session...")
        print("=" * 60)

        session_task = (
            "This is an interactive session. "
            "You can ask the user which request to process."
        )
        async for event in agent.run(session_task):
            if isinstance(event, SelectSpeakerEvent):
                # Show real-time agent selection
                selected_agents = event.content
                if selected_agents:
                    print(f"🤖 Agent selected: {selected_agents[0]}")

            elif isinstance(event, TextMessage):
                # Show agent messages (full content)
                source = event.source
                content = event.content
                print(f"💬 {source}: {content}")

            elif isinstance(event, ToolCallRequestEvent):
                # Show tool call request details
                source = event.source
                tool_calls = event.content
                print(f"🔨 {source}: Tool request")
                for i, tool_call in enumerate(tool_calls):
                    print(f"   Tool {i+1}: {tool_call.name}")
                    if hasattr(tool_call, "arguments") and tool_call.arguments:
                        args_str = str(tool_call.arguments)
                        if len(args_str) > 150:
                            args_str = args_str[:150] + "..."
                        print(f"   Arguments: {args_str}")

            elif isinstance(event, ToolCallExecutionEvent):
                # Show tool call execution details
                source = event.source
                tool_calls = event.content
                print(f"🔧 {source}: Tool execution")
                for i, tool_call in enumerate(tool_calls):
                    # tool_call is a FunctionExecutionResult
                    print(f"   Tool {i+1}: {tool_call.name}")
                    if hasattr(tool_call, "content") and tool_call.content:
                        # Truncate long content for readability
                        content_str = str(tool_call.content)
                        if len(content_str) > 200:
                            content_str = content_str[:200] + "..."
                        print(f"   Result: {content_str}")

            elif isinstance(event, Response):
                # Show detailed response information
                source = getattr(event.chat_message, "source", "unknown")
                content = getattr(
                    event.chat_message, "content", str(event.chat_message)
                )
                msg_type = type(event.chat_message).__name__
                print(f"📤 {source}: Response ({msg_type})")

                # Show inner messages details
                if hasattr(event, "inner_messages") and event.inner_messages:
                    print(f"   Inner messages: {len(event.inner_messages)}")
                    for j, inner_msg in enumerate(
                        event.inner_messages[:3]
                    ):  # Show first 3
                        inner_type = type(inner_msg).__name__
                        inner_source = getattr(inner_msg, "source", "unknown")
                        print(f"     {j+1}. {inner_type} from {inner_source}")
                    if len(event.inner_messages) > 3:
                        print(f"     ... and {len(event.inner_messages) - 3} more")

                # Show content with more context
                content_str = str(content)
                if len(content_str) > 200:
                    content_str = content_str[:200] + "..."
                print(f"   Content: {content_str}")

                # Show additional response attributes
                if hasattr(event, "chat_message"):
                    chat_msg = event.chat_message
                    if hasattr(chat_msg, "models_usage") and chat_msg.models_usage:
                        print(f"   Model usage: {chat_msg.models_usage}")

            elif isinstance(event, TaskResult):
                print("=" * 60)
                print("✅ Session completed!")
                if event.messages:
                    last_message = event.messages[-1]
                    if isinstance(last_message, TextMessage):
                        print(f"💬 {last_message.source}: {last_message.content}")

    except KeyboardInterrupt:
        print("\n⚠️ Session interrupted by user.")


def main():
    """Main entry point for the ra-orchestrator CLI command."""
    parser = argparse.ArgumentParser(
        description="Robotsix Agents Orchestrator - Multi-agent task orchestration"
    )
    parser.add_argument(
        "--agent-name",
        default="orchestrator",
        help="Agent name for configuration lookup (default: orchestrator)",
    )
    parser.add_argument("--task", help="Task description to orchestrate")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Start interactive orchestration session (requires UserProxy)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="WARNING",
        help="Set the logging level (default: WARNING)",
    )
    args = parser.parse_args()

    # Configure logging based on the specified level
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Determine mode
    if args.task:
        # Single task mode - no user proxy needed
        enable_user_proxy = False
        mode = "single"
    elif args.interactive:
        # Interactive mode - requires user proxy
        enable_user_proxy = True
        mode = "interactive"
    else:
        # Default to interactive mode
        enable_user_proxy = True
        mode = "interactive"

    try:
        # Create the orchestrator agent
        agent = create_orchestrator_agent_from_config(
            agent_name=args.agent_name, enable_user_proxy=enable_user_proxy
        )

        if mode == "single":
            # Single task mode
            result = asyncio.run(run_task_with_streaming(agent, args.task))
            print(f"\n📝 Final result: {result}")
        else:
            # Interactive mode with UserProxy
            asyncio.run(interactive_session(agent))

    except (ConfigError, ModelProviderError, DependencyMissingError) as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
