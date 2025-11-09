"""
Custom Function Tools Module.

Provides weather and time information tools with proper type annotations
for Azure AI Agents integration.
"""

from datetime import datetime, timezone
from random import randint
from typing import Annotated

from pydantic import Field


def get_weather(
    location: Annotated[str, Field(description="The location to get the weather for.")],
) -> str:
    """
    Get the weather for a given location.

    This is a simulated weather service that returns random weather conditions.
    In production, this would connect to a real weather API.

    :param location: The location to get weather information for
    :return: Weather description string
    """
    conditions = ["sunny", "cloudy", "rainy", "stormy"]
    temperature = randint(10, 30)
    condition = conditions[randint(0, 3)]

    return f"The weather in {location} is {condition} with a high of {temperature}°C."


def get_time() -> str:
    """
    Get the current UTC time.

    Returns the current time in UTC timezone formatted as a readable string.

    :return: Current UTC time string
    """
    current_time = datetime.now(timezone.utc)
    return f"The current UTC time is {current_time.strftime('%Y-%m-%d %H:%M:%S')}."
