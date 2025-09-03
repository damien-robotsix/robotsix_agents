from typing import Annotated, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import zoneinfo
import caldav
from robotsix_agents.core import get_config_manager


def create_calendar_event(
    summary: Annotated[str, "The title/summary of the event"],
    start_time: Annotated[str, "Start time in ISO format (YYYY-MM-DDTHH:MM:SS)"],
    end_time: Annotated[str, "End time in ISO format (YYYY-MM-DDTHH:MM:SS)"],
    description: Annotated[Optional[str], "Description of the event"] = None,
    location: Annotated[Optional[str], "Location of the event"] = None,
) -> str:
    """
    Create a new calendar event using CalDAV.

    Args:
        summary: The title/summary of the event
        start_time: Start time in ISO format (YYYY-MM-DDTHH:MM:SS)
        end_time: End time in ISO format (YYYY-MM-DDTHH:MM:SS)
        description: Description of the event (optional)
        location: Location of the event (optional)

    Returns:
        str: Success message with event details
    """
    try:
        # Get configuration manager and calendar configuration
        config_manager = get_config_manager()
        agent_config = config_manager.get_agent_config("calendar_task")
        caldav_config = agent_config.get("caldav", {})

        # Get user timezone from config or default to Europe/Paris
        user_timezone = agent_config.get("timezone", "Europe/Paris")
        try:
            tz = zoneinfo.ZoneInfo(user_timezone)
        except Exception:
            # Fallback to Europe/Paris if invalid timezone
            tz = zoneinfo.ZoneInfo("Europe/Paris")

        # Validate required configuration
        if (
            not caldav_config.get("url")
            or not caldav_config.get("username")
            or not caldav_config.get("password")
        ):
            return (
                "Error: CalDAV configuration missing. "
                "Please configure url, username, and password."
            )

        # Parse datetime strings and handle timezone awareness
        try:
            start_dt = datetime.fromisoformat(start_time)
            end_dt = datetime.fromisoformat(end_time)

            # If datetimes are naive (no timezone), assume user's local timezone
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=tz)
            if end_dt.tzinfo is None:
                end_dt = end_dt.replace(tzinfo=tz)

        except ValueError as e:
            return f"Error: Invalid datetime format. Use YYYY-MM-DDTHH:MM:SS. {e}"

        # Validate end time is after start time
        if end_dt <= start_dt:
            return "Error: End time must be after start time."

        # Connect to CalDAV server
        client = caldav.DAVClient(
            url=caldav_config["url"],
            username=caldav_config["username"],
            password=caldav_config["password"],
            ssl_verify_cert=caldav_config.get("verify_ssl", True),
        )

        # Get principal and calendar
        principal = client.principal()  # type: ignore
        calendars = principal.calendars()

        if not calendars:
            return "Error: No calendars found on the CalDAV server."

        # Use specified calendar or first available
        calendar_name = caldav_config.get("calendar_name")
        if calendar_name:
            target_calendar = None
            for cal in calendars:
                if cal.name == calendar_name:
                    target_calendar = cal
                    break
            if not target_calendar:
                available = [cal.name for cal in calendars]
                return (
                    f"Error: Calendar '{calendar_name}' not found. "
                    f"Available calendars: {available}"
                )
        else:
            target_calendar = calendars[0]

        # Create iCalendar event with proper timezone handling
        # Convert to UTC for iCalendar format
        start_utc = start_dt.astimezone(timezone.utc)
        end_utc = end_dt.astimezone(timezone.utc)

        event_data = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//robotsix-agents//calendar-agent//EN",
            "BEGIN:VEVENT",
            f"DTSTART:{start_utc.strftime('%Y%m%dT%H%M%SZ')}",
            f"DTEND:{end_utc.strftime('%Y%m%dT%H%M%SZ')}",
            f"SUMMARY:{summary}",
            f"UID:{datetime.now().strftime('%Y%m%d%H%M%S')}@robotsix-agents",
            "DTSTAMP:" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        ]

        if description:
            event_data.append(f"DESCRIPTION:{description}")
        if location:
            event_data.append(f"LOCATION:{location}")

        event_data.extend(["END:VEVENT", "END:VCALENDAR"])

        # Add event to calendar
        event_ical = "\r\n".join(event_data)
        target_calendar.save_event(event_ical)  # type: ignore

        # Format display times in user's timezone for confirmation
        start_local = start_dt.strftime("%Y-%m-%d %H:%M:%S %Z")
        end_local = end_dt.strftime("%Y-%m-%d %H:%M:%S %Z")

        return (
            f"Successfully created calendar event: '{summary}' "
            f"from {start_local} to {end_local}"
        )

    except caldav.error.AuthorizationError:
        return "Error: Authentication failed. Please check your CalDAV credentials."
    except caldav.error.NotFoundError:
        return "Error: CalDAV server or calendar not found. Please check the URL."
    except Exception as e:
        return f"Error creating calendar event: {str(e)}"


def _get_caldav_client_and_calendar():
    """
    Helper function to get CalDAV client and calendar.

    Returns:
        tuple: (client, calendar, user_timezone) or (None, None, None) if error
    """
    try:
        config_manager = get_config_manager()
        agent_config = config_manager.get_agent_config("calendar_task")
        caldav_config = agent_config.get("caldav", {})

        # Get user timezone from config or default to Europe/Paris
        user_timezone = agent_config.get("timezone", "Europe/Paris")
        try:
            tz = zoneinfo.ZoneInfo(user_timezone)
        except Exception:
            tz = zoneinfo.ZoneInfo("Europe/Paris")
            user_timezone = "Europe/Paris"

        # Validate required configuration
        if (
            not caldav_config.get("url")
            or not caldav_config.get("username")
            or not caldav_config.get("password")
        ):
            return None, None, None

        # Connect to CalDAV server
        client = caldav.DAVClient(
            url=caldav_config["url"],
            username=caldav_config["username"],
            password=caldav_config["password"],
            ssl_verify_cert=caldav_config.get("verify_ssl", True),
        )

        # Get principal and calendar
        principal = client.principal()
        calendars = principal.calendars()

        if not calendars:
            return None, None, None

        # Use specified calendar or first available
        calendar_name = caldav_config.get("calendar_name")
        if calendar_name:
            target_calendar = None
            for cal in calendars:
                if cal.name == calendar_name:
                    target_calendar = cal
                    break
            if not target_calendar:
                return None, None, None
        else:
            target_calendar = calendars[0]

        return client, target_calendar, user_timezone

    except Exception:
        return None, None, None


def _parse_calendar_event(event: Any, user_timezone: str) -> Dict[str, Any]:
    """
    Parse a CalDAV event into a convenient dictionary format.

    Args:
        event: CalDAV event object
        user_timezone: User's timezone string

    Returns:
        Dict with event details
    """
    try:
        tz = zoneinfo.ZoneInfo(user_timezone)
    except Exception:
        tz = zoneinfo.ZoneInfo("Europe/Paris")

    try:
        # Get event data
        event_data = event.data

        # Parse basic info
        summary = ""
        description = ""
        location = ""
        start_time = None
        end_time = None

        # Extract fields from iCalendar data
        lines = event_data.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("SUMMARY:"):
                summary = line[8:]
            elif line.startswith("DESCRIPTION:"):
                description = line[12:]
            elif line.startswith("LOCATION:"):
                location = line[9:]
            elif line.startswith("DTSTART:"):
                dt_str = line[8:]
                if dt_str.endswith("Z"):  # UTC time
                    start_time = datetime.strptime(dt_str, "%Y%m%dT%H%M%SZ").replace(
                        tzinfo=timezone.utc
                    )
                else:
                    # Try to parse without timezone first
                    try:
                        start_time = datetime.strptime(dt_str, "%Y%m%dT%H%M%S")
                        start_time = start_time.replace(tzinfo=tz)
                    except ValueError:
                        # Try parsing with timezone info
                        start_time = datetime.fromisoformat(dt_str)
            elif line.startswith("DTEND:"):
                dt_str = line[6:]
                if dt_str.endswith("Z"):  # UTC time
                    end_time = datetime.strptime(dt_str, "%Y%m%dT%H%M%SZ").replace(
                        tzinfo=timezone.utc
                    )
                else:
                    try:
                        end_time = datetime.strptime(dt_str, "%Y%m%dT%H%M%S")
                        end_time = end_time.replace(tzinfo=tz)
                    except ValueError:
                        end_time = datetime.fromisoformat(dt_str)

        # Convert times to user timezone for display
        if start_time:
            start_local = start_time.astimezone(tz)
        else:
            start_local = None

        if end_time:
            end_local = end_time.astimezone(tz)
        else:
            end_local = None

        return {
            "summary": summary,
            "description": description,
            "location": location,
            "start_time": (
                start_local.strftime("%Y-%m-%d %H:%M:%S %Z")
                if start_local
                else "Unknown"
            ),
            "end_time": (
                end_local.strftime("%Y-%m-%d %H:%M:%S %Z") if end_local else "Unknown"
            ),
            "start_datetime": start_local,
            "end_datetime": end_local,
        }

    except Exception as e:
        return {
            "summary": "Error parsing event",
            "description": f"Parse error: {str(e)}",
            "location": "",
            "start_time": "Unknown",
            "end_time": "Unknown",
            "start_datetime": None,
            "end_datetime": None,
        }


def get_today_events(
    include_all_day: Annotated[bool, "Include all-day events (default: True)"] = True,
) -> str:
    """
    Get all events for today.

    Args:
        include_all_day: Whether to include all-day events (default: True)

    Returns:
        str: Formatted list of today's events
    """
    try:
        client, calendar, user_timezone = _get_caldav_client_and_calendar()
        if not client or not calendar:
            return "Error: Could not connect to calendar. Please check your CalDAV configuration."

        # Get user timezone
        try:
            tz = zoneinfo.ZoneInfo(user_timezone or "Europe/Paris")
        except Exception:
            tz = zoneinfo.ZoneInfo("Europe/Paris")

        # Get today's date range
        now = datetime.now(tz)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)

        # Search for events
        events = calendar.search(
            start=start_of_day, end=end_of_day, event=True, expand=True
        )

        if not events:
            return f"No events found for today ({now.strftime('%Y-%m-%d')})."

        # Parse and format events
        event_list = []
        for event in events:
            parsed_event = _parse_calendar_event(event, user_timezone)
            event_list.append(parsed_event)

        # Sort events by start time
        event_list.sort(
            key=lambda x: (
                x["start_datetime"]
                if x["start_datetime"]
                else datetime.min.replace(tzinfo=tz)
            )
        )

        # Format output
        result = f"Events for today ({now.strftime('%A, %B %d, %Y')}):\n\n"
        for i, event in enumerate(event_list, 1):
            result += f"{i}. {event['summary']}\n"
            result += f"   Time: {event['start_time']} - {event['end_time']}\n"
            if event["location"]:
                result += f"   Location: {event['location']}\n"
            if event["description"]:
                result += f"   Description: {event['description']}\n"
            result += "\n"

        return result.strip()

    except Exception as e:
        return f"Error retrieving today's events: {str(e)}"


def get_events_date_range(
    start_date: Annotated[str, "Start date in YYYY-MM-DD format"],
    end_date: Annotated[str, "End date in YYYY-MM-DD format"],
) -> str:
    """
    Get events for a specific date range.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        str: Formatted list of events in the date range
    """
    try:
        client, calendar, user_timezone = _get_caldav_client_and_calendar()
        if not client or not calendar:
            return "Error: Could not connect to calendar. Please check your CalDAV configuration."

        # Get user timezone
        try:
            tz = zoneinfo.ZoneInfo(user_timezone)
        except Exception:
            tz = zoneinfo.ZoneInfo("Europe/Paris")

        # Parse date strings
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=tz)
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59, tzinfo=tz
            )
        except ValueError as e:
            return f"Error: Invalid date format. Use YYYY-MM-DD. {e}"

        # Validate date range
        if end_dt < start_dt:
            return "Error: End date must be after or equal to start date."

        # Search for events
        events = calendar.search(start=start_dt, end=end_dt, event=True, expand=True)

        if not events:
            return f"No events found from {start_date} to {end_date}."

        # Parse and format events
        event_list = []
        for event in events:
            parsed_event = _parse_calendar_event(event, user_timezone)
            event_list.append(parsed_event)

        # Sort events by start time
        event_list.sort(
            key=lambda x: (
                x["start_datetime"]
                if x["start_datetime"]
                else datetime.min.replace(tzinfo=tz)
            )
        )

        # Format output
        result = f"Events from {start_date} to {end_date}:\n\n"
        for i, event in enumerate(event_list, 1):
            result += f"{i}. {event['summary']}\n"
            result += f"   Time: {event['start_time']} - {event['end_time']}\n"
            if event["location"]:
                result += f"   Location: {event['location']}\n"
            if event["description"]:
                result += f"   Description: {event['description']}\n"
            result += "\n"

        return result.strip()

    except Exception as e:
        return f"Error retrieving events for date range: {str(e)}"


def get_events_period(
    period: Annotated[
        str,
        "Time period: 'this_week', 'next_week', 'this_month', 'next_month', 'tomorrow', 'yesterday'",
    ],
) -> str:
    """
    Get events for common time periods.

    Args:
        period: Time period ('this_week', 'next_week', 'this_month', 'next_month', 'tomorrow', 'yesterday')

    Returns:
        str: Formatted list of events for the specified period
    """
    try:
        client, calendar, user_timezone = _get_caldav_client_and_calendar()
        if not client or not calendar:
            return "Error: Could not connect to calendar. Please check your CalDAV configuration."

        # Get user timezone
        try:
            tz = zoneinfo.ZoneInfo(user_timezone)
        except Exception:
            tz = zoneinfo.ZoneInfo("Europe/Paris")

        now = datetime.now(tz)

        # Calculate date range based on period
        if period == "tomorrow":
            start_dt = (now + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            end_dt = start_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
            period_name = f"Tomorrow ({start_dt.strftime('%A, %B %d, %Y')})"
        elif period == "yesterday":
            start_dt = (now - timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            end_dt = start_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
            period_name = f"Yesterday ({start_dt.strftime('%A, %B %d, %Y')})"
        elif period == "this_week":
            # Monday to Sunday
            days_since_monday = now.weekday()
            start_dt = (now - timedelta(days=days_since_monday)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            end_dt = (start_dt + timedelta(days=6)).replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
            period_name = f"This week ({start_dt.strftime('%B %d')} - {end_dt.strftime('%B %d, %Y')})"
        elif period == "next_week":
            # Next Monday to Sunday
            days_since_monday = now.weekday()
            next_monday = now + timedelta(days=(7 - days_since_monday))
            start_dt = next_monday.replace(hour=0, minute=0, second=0, microsecond=0)
            end_dt = (start_dt + timedelta(days=6)).replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
            period_name = f"Next week ({start_dt.strftime('%B %d')} - {end_dt.strftime('%B %d, %Y')})"
        elif period == "this_month":
            start_dt = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # Get last day of month
            if now.month == 12:
                next_month = now.replace(year=now.year + 1, month=1)
            else:
                next_month = now.replace(month=now.month + 1)
            end_dt = (next_month - timedelta(days=1)).replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
            period_name = f"This month ({now.strftime('%B %Y')})"
        elif period == "next_month":
            if now.month == 12:
                next_month_start = now.replace(year=now.year + 1, month=1, day=1)
            else:
                next_month_start = now.replace(month=now.month + 1, day=1)
            start_dt = next_month_start.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            # Get last day of next month
            if next_month_start.month == 12:
                month_after_next = next_month_start.replace(
                    year=next_month_start.year + 1, month=1
                )
            else:
                month_after_next = next_month_start.replace(
                    month=next_month_start.month + 1
                )
            end_dt = (month_after_next - timedelta(days=1)).replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
            period_name = f"Next month ({next_month_start.strftime('%B %Y')})"
        else:
            return f"Error: Invalid period '{period}'. Valid periods: 'this_week', 'next_week', 'this_month', 'next_month', 'tomorrow', 'yesterday'"

        # Search for events
        events = calendar.search(start=start_dt, end=end_dt, event=True, expand=True)

        if not events:
            return f"No events found for {period_name.lower()}."

        # Parse and format events
        event_list = []
        for event in events:
            parsed_event = _parse_calendar_event(event, user_timezone)
            event_list.append(parsed_event)

        # Sort events by start time
        event_list.sort(
            key=lambda x: (
                x["start_datetime"]
                if x["start_datetime"]
                else datetime.min.replace(tzinfo=tz)
            )
        )

        # Format output
        result = f"Events for {period_name}:\n\n"
        for i, event in enumerate(event_list, 1):
            result += f"{i}. {event['summary']}\n"
            result += f"   Time: {event['start_time']} - {event['end_time']}\n"
            if event["location"]:
                result += f"   Location: {event['location']}\n"
            if event["description"]:
                result += f"   Description: {event['description']}\n"
            result += "\n"

        return result.strip()

    except Exception as e:
        return f"Error retrieving events for {period}: {str(e)}"


def search_events(
    query: Annotated[
        str, "Search query to find in event titles, descriptions, or locations"
    ],
    days_ahead: Annotated[int, "Number of days ahead to search (default: 30)"] = 30,
) -> str:
    """
    Search for events containing specific text.

    Args:
        query: Search query to find in event titles, descriptions, or locations
        days_ahead: Number of days ahead to search (default: 30)

    Returns:
        str: Formatted list of matching events
    """
    try:
        client, calendar, user_timezone = _get_caldav_client_and_calendar()
        if not client or not calendar:
            return "Error: Could not connect to calendar. Please check your CalDAV configuration."

        # Get user timezone
        try:
            tz = zoneinfo.ZoneInfo(user_timezone)
        except Exception:
            tz = zoneinfo.ZoneInfo("Europe/Paris")

        # Set search date range (from today to specified days ahead)
        now = datetime.now(tz)
        start_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_dt = (now + timedelta(days=days_ahead)).replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

        # Search for events
        events = calendar.search(start=start_dt, end=end_dt, event=True, expand=True)

        if not events:
            return f"No events found in the next {days_ahead} days."

        # Parse events and filter by query
        matching_events = []
        query_lower = query.lower()

        for event in events:
            parsed_event = _parse_calendar_event(event, user_timezone)

            # Check if query matches in summary, description, or location
            if (
                query_lower in parsed_event["summary"].lower()
                or query_lower in parsed_event["description"].lower()
                or query_lower in parsed_event["location"].lower()
            ):
                matching_events.append(parsed_event)

        if not matching_events:
            return f"No events found matching '{query}' in the next {days_ahead} days."

        # Sort events by start time
        matching_events.sort(
            key=lambda x: (
                x["start_datetime"]
                if x["start_datetime"]
                else datetime.min.replace(tzinfo=tz)
            )
        )

        # Format output
        result = f"Events matching '{query}' (next {days_ahead} days):\n\n"
        for i, event in enumerate(matching_events, 1):
            result += f"{i}. {event['summary']}\n"
            result += f"   Time: {event['start_time']} - {event['end_time']}\n"
            if event["location"]:
                result += f"   Location: {event['location']}\n"
            if event["description"]:
                result += f"   Description: {event['description']}\n"
            result += "\n"

        return result.strip()

    except Exception as e:
        return f"Error searching events: {str(e)}"
