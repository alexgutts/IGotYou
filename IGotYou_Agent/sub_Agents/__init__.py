"""
Sub-Agents Module - Specialized Agents for the IGotYou Pipeline

This module exports all sub-agents used in the IGotYou discovery pipeline.
Each agent handles a specific phase of finding hidden outdoor gems.

AGENT PIPELINE ORDER:
    1. discovery_agent      → Finds candidate places using Google Places API
    2. analysis_agent       → Filters candidates based on hidden gem criteria
    3. recommendation_agent → Generates insights and formats final output
    4. weather_agent        → Adds weather data and clothing recommendations

USAGE:
    from .sub_Agents import (
        discovery_agent,
        analysis_agent,
        recommendation_agent,
        weather_agent,
    )
"""

# Import each agent from its respective module
from .discovery_agent import discovery_agent
from .analysis_agent import analysis_agent
from .Recommendation_agent import recommendation_agent
from .weather_agent import weather_agent  # NEW: MCP Weather Integration

# Define what gets exported when using "from sub_Agents import *"
__all__ = [
    "discovery_agent",
    "analysis_agent", 
    "recommendation_agent",
    "weather_agent",  # NEW: MCP Weather Integration
]
