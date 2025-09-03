from datetime import datetime, timezone
import zoneinfo
from autogen_agentchat.agents import AssistantAgent
from autogen_core.tools import FunctionTool
from robotsix_agents.core import get_config_manager
from .tools import (
    create_calendar_event,
    get_today_events,
    get_events_date_range,
    get_events_period,
    search_events,
)


def create_agent():
    """
    Create a calendar_task assistant agent with CalDAV capabilities.

    Returns:
        AssistantAgent: The configured calendar_task agent
    """
    # Get configuration manager
    config_manager = get_config_manager()

    # Get model client from configuration manager
    model_client = config_manager.get_model_client("calendar_task")

    # Get agent configuration for max_tool_iterations
    agent_config = config_manager.get_agent_config("calendar_task")
    max_tool_iterations = agent_config.get("max_tool_iterations", 10)

    # Get user timezone from agent config or default to Europe/Paris
    user_timezone = agent_config.get("timezone", "Europe/Paris")
    try:
        tz = zoneinfo.ZoneInfo(user_timezone)
    except Exception:
        # Fallback to Europe/Paris if invalid timezone
        tz = zoneinfo.ZoneInfo("Europe/Paris")

    # Get current date and time in user's timezone
    current_time = datetime.now(tz)
    utc_time = datetime.now(timezone.utc)

    # Create system message with current date/time awareness
    system_message = f"""You are a helpful calendar assistant with access to CalDAV \
    calendar management tools.
    
    Current date and time information:
    - Local Time ({user_timezone}): {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}
    - UTC Time: {utc_time.strftime('%Y-%m-%d %H:%M:%S')}
    - Day: {current_time.strftime('%A')}
    - Date: {current_time.strftime('%B %d, %Y')}
    
    You can help users:
    - Create calendar events and appointments
    - View today's agenda and upcoming events
    - Search through their calendar
    - Get events for specific date ranges or periods
    - Manage their calendar efficiently
    
    Available tools:
    - create_calendar_event: Create new events
    - get_today_events: Get all events for today
    - get_events_date_range: Get events for a specific date range
    - get_events_period: Get events for common periods (this week, next week, this month, etc.)
    - search_events: Search for events by keywords
    
    When users mention relative times like "tomorrow", "next week", "in 2 hours", use the \
    current date and time above to calculate the exact dates and times. Always use ISO \
    format (YYYY-MM-DDTHH:MM:SS) when creating events. The user is in timezone \
    {user_timezone}, so interpret all times relative to this timezone unless explicitly \
    specified otherwise.
    
    For agenda queries, use the most appropriate tool:
    - "What's on my calendar today?" → use get_today_events
    - "What do I have next week?" → use get_events_period with "next_week"
    - "Show me events from March 1 to March 15" → use get_events_date_range
    - "Find my dentist appointment" → use search_events with "dentist"
    
    Always present calendar information in a clear, organized format."""

    # Create all calendar tools
    create_event_tool = FunctionTool(
        create_calendar_event,
        name="create_calendar_event",
        description="Create a new calendar event using CalDAV",
    )

    today_events_tool = FunctionTool(
        get_today_events,
        name="get_today_events",
        description="Get all events for today",
    )

    date_range_tool = FunctionTool(
        get_events_date_range,
        name="get_events_date_range",
        description="Get events for a specific date range (YYYY-MM-DD format)",
    )

    period_tool = FunctionTool(
        get_events_period,
        name="get_events_period",
        description="Get events for common periods (this_week, next_week, this_month, next_month, tomorrow, yesterday)",
    )

    search_tool = FunctionTool(
        search_events,
        name="search_events",
        description="Search for events by keywords in title, description, or location",
    )

    # Create assistant agent with all calendar_task tools
    calendar_task_agent = AssistantAgent(
        max_tool_iterations=max_tool_iterations,
        name="calendar_task",
        description="Agent that can create, retrieve, search, and manage calendar events using CalDAV. Know the current date and time.",
        model_client=model_client,
        tools=[
            create_event_tool,
            today_events_tool,
            date_range_tool,
            period_tool,
            search_tool,
        ],
        system_message=system_message,
    )

    return calendar_task_agent
