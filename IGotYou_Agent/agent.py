"""
IGotYou Root Agent - Main Orchestrator for Hidden Gem Discovery

This is the main entry point for the IGotYou AI agent system.
It uses a SequentialAgent to coordinate multiple specialized sub-agents
in a pipeline fashion.

AGENT PIPELINE:
    1. Discovery Agent  → Finds candidate places using Google Places API
    2. Analysis Agent   → Filters candidates to find true "hidden gems"
    3. Recommendation Agent → Generates human-friendly insights and formats output
    4. Weather Agent    → Adds weather data and clothing recommendations (NEW!)

USAGE:
    - Import `root_agent` and `runner` from this module
    - Use `await runner.run_debug(query)` to process queries
    - The backend (FastAPI) imports this to handle API requests
"""

import asyncio

# Google ADK imports for building the agent
from google.adk.agents import SequentialAgent
from google.adk.models.google_llm import Gemini
from google.genai import types
from google.adk.runners import InMemoryRunner

# Import API key configuration from our config module
from .config import GOOGLE_API_KEY

# Import specialized sub-agents for the multi-agent workflow
# Each agent handles a specific part of the discovery pipeline
from .sub_Agents import (
    analysis_agent,        # Phase 2: Filter & analyze candidates
    discovery_agent,       # Phase 1: Find raw candidates
    recommendation_agent,  # Phase 3: Format recommendations
    weather_agent,         # Phase 4: Add weather + clothing tips (NEW!)
)


# ============================================================================
# NETWORK CONFIGURATION
# ============================================================================

# Robust retry configuration for API calls
# This ensures reliable communication even with unstable connections
retry_config = types.HttpRetryOptions(
    attempts=5,              # Maximum retry attempts before giving up
    exp_base=7,              # Delay multiplier for exponential backoff
    initial_delay=1,         # Initial delay before first retry (in seconds)
    http_status_codes=[      # Retry on these HTTP error codes:
        429,                 # - Rate limited (too many requests)
        500,                 # - Internal server error
        503,                 # - Service unavailable
        504                  # - Gateway timeout
    ]
)


# ============================================================================
# ROOT AGENT DEFINITION
# ============================================================================

# Main orchestrator agent that coordinates the entire workflow
# SequentialAgent executes sub-agents in order, passing output from one to the next
root_agent = SequentialAgent(
    name="IGOTYOU_Agent",
    
    # High-level description of what this agent does
    description="""
    Your role is to manage user interaction and delegate to specialized 
    sub-agents to find hidden outdoor gems. You coordinate the discovery 
    pipeline from initial search to final recommendations with weather info.
    """,
    
    # Sub-agents are executed in this exact sequence:
    # Each agent's output becomes the next agent's input
    sub_agents=[
        discovery_agent,       # 1️⃣ Find raw candidates using Google Places API
        analysis_agent,        # 2️⃣ Filter candidates and fetch detailed reviews
        recommendation_agent,  # 3️⃣ Generate human-friendly insights & format JSON
        weather_agent,         # 4️⃣ Add weather data + clothing recommendations (NEW!)
    ],
    
    # Note: Root agent doesn't need tools - sub-agents handle all tool execution
)


# ============================================================================
# RUNNER INSTANCE
# ============================================================================

# Create the runner instance for executing agent queries
# InMemoryRunner is suitable for development and single-server deployments
runner = InMemoryRunner(agent=root_agent)


# ============================================================================
# INTERACTIVE MODE (for testing)
# ============================================================================

async def main():
    """
    Main function to run the agent in interactive mode.
    
    This provides a REPL (Read-Eval-Print Loop) interface for testing
    the agent directly from the command line.
    
    Usage:
        python -m IGotYou_Agent.agent
    
    Example:
        You: quiet beach in California
        Agent: [Returns JSON with hidden gem recommendations]
    """
    print(f"✅ Agent {root_agent.name} initialized.")
    print("\n🤖 I GOT YOU Agent is ready! (Type 'exit' to quit)")
    print("📌 Try: 'quiet beach in California' or 'hidden hiking trails in Oregon'")
    
    while True:
        try:
            # Get user input
            user_input = input("\nYou: ")
            
            # Allow user to exit gracefully
            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye! Get you later 👋")
                break
            
            # Skip empty input
            if not user_input.strip():
                continue
            
            # Run the agent with the user's query
            print("\n🔄 Processing your request...")
            response = await runner.run_debug(user_input)
            print(f"\nAgent: {response}")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye! Get you later 👋")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Clean up: close the runner when done
    await runner.close()


# ============================================================================
# ENTRY POINT
# ============================================================================

# Only run main() if this script is executed directly (not when imported)
# This allows the agent to be imported as a module without running interactive mode
if __name__ == "__main__":
    asyncio.run(main())
