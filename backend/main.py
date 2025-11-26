"""
FastAPI Backend Wrapper for IGotYou Agent

This file provides a REST API interface to the IGotYou Python agent.
It handles CORS, request validation, and response formatting.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import IGotYou_Agent
sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import asyncio
import re

# Import the agent
from IGotYou_Agent import root_agent, runner

app = FastAPI(
    title="I Got You API",
    description="API for discovering hidden outdoor gems",
    version="1.0.0"
)

# CORS Configuration
allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic Models
class DiscoveryRequest(BaseModel):
    searchQuery: str = Field(..., min_length=10, max_length=200)


class Coordinates(BaseModel):
    lat: float
    lng: float


class Analysis(BaseModel):
    whySpecial: str
    bestTime: str
    insiderTip: str


class HiddenGem(BaseModel):
    placeName: str
    address: str
    coordinates: Coordinates
    rating: float
    reviewCount: int
    photos: List[str]
    analysis: Analysis


class DiscoveryResponse(BaseModel):
    gems: List[HiddenGem]
    processingTime: float
    query: str


def parse_agent_response(raw_response: str, query: str) -> DiscoveryResponse:
    """
    Parse the agent's text response into structured JSON.

    This is a simplified parser. In production, you'd want more robust parsing
    or have the agent return structured JSON directly.
    """
    # For now, return mock data
    # TODO: Implement proper parsing of agent response
    mock_gems = [
        HiddenGem(
            placeName="Hidden Beach Example",
            address="Example Location, Bali, Indonesia",
            coordinates=Coordinates(lat=-8.6569, lng=115.1381),
            rating=4.6,
            reviewCount=142,
            photos=[
                "https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=800",
            ],
            analysis=Analysis(
                whySpecial="This spot offers amazing waves and fewer crowds.",
                bestTime="Visit early morning for the best experience.",
                insiderTip="Locals recommend bringing your own snacks."
            )
        )
    ]

    return DiscoveryResponse(
        gems=mock_gems,
        processingTime=15.0,
        query=query
    )


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "I Got You API",
        "version": "1.0.0"
    }


@app.post("/api/discover", response_model=DiscoveryResponse)
async def discover_gems(request: DiscoveryRequest):
    """
    Discover hidden outdoor gems based on search query.

    Args:
        request: Discovery request with search query

    Returns:
        DiscoveryResponse with found hidden gems
    """
    try:
        import time
        start_time = time.time()

        # Run the agent
        response = await runner.run_debug(request.searchQuery)

        # Parse response into structured format
        result = parse_agent_response(str(response), request.searchQuery)

        # Calculate actual processing time
        result.processingTime = time.time() - start_time

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    try:
        await runner.close()
    except:
        pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
