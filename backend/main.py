"""
FastAPI Backend Wrapper for IGotYou Agent

This file provides a REST API interface to the IGotYou Python agent.
It handles CORS, request validation, and response formatting.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import IGotYou_Agent
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
# Also add IGotYou_Agent directory to path so 'config' and 'sub_Agents' imports work
sys.path.insert(0, str(project_root / "IGotYou_Agent"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import asyncio
import re

# Import the agent (must be after path setup)
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


def parse_agent_response(raw_response: str, query: str) -> dict:
    """
    Parse the agent's JSON response. The recommendation agent now returns clean JSON.
    """
    import json

    try:
        response_text = str(raw_response).strip()
        print(f"[Backend] Attempting to parse JSON response (length: {len(response_text)})")

        # Remove markdown code blocks if present
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            print(f"[Backend] Found JSON in code block")
        else:
            # Look for JSON object with "gems" array
            json_match = re.search(r'\{\s*"gems"\s*:\s*\[.*?\]\s*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                print(f"[Backend] Found JSON with gems array")
            else:
                # Try to extract first valid JSON object
                json_str = response_text
                # Remove any leading/trailing text
                start_idx = json_str.find('{')
                if start_idx != -1:
                    json_str = json_str[start_idx:]

        # Parse the JSON
        parsed_data = json.loads(json_str)
        print(f"[Backend] Successfully parsed JSON. Keys: {list(parsed_data.keys())}")

        # Validate and return
        if "gems" in parsed_data and isinstance(parsed_data["gems"], list):
            gems_count = len(parsed_data["gems"])
            print(f"[Backend] Found {gems_count} gems in response")
            return parsed_data
        else:
            print(f"[Backend] No gems array found, returning empty")
            return {"gems": []}

    except json.JSONDecodeError as e:
        print(f"[Backend] JSON decode error: {e}")
        print(f"[Backend] Response preview: {response_text[:500]}...")
        return {"gems": []}
    except Exception as e:
        print(f"[Backend] Error parsing agent response: {e}")
        print(f"[Backend] Response preview: {response_text[:500]}...")
        return {"gems": []}


def transform_gem_format(gem: dict, full_response: str = "") -> dict:
    """
    Transform analysis agent's gem format to frontend's expected format.
    
    Analysis agent format:
    {
        "name": "...",
        "rating": ...,
        "review_count": ...,
        "address": "...",
        "map_url": "...",
        "reviews_content": "...",
        "loc": {"lat": ..., "lng": ...}  # from discovery agent (might not be present)
    }
    
    Frontend format:
    {
        "placeName": "...",
        "address": "...",
        "coordinates": {"lat": ..., "lng": ...},
        "rating": ...,
        "reviewCount": ...,
        "photos": [...],
        "analysis": {
            "whySpecial": "...",
            "bestTime": "...",
            "insiderTip": "..."
        }
    }
    """
    # Extract coordinates (might be in loc field, or need to extract from map_url)
    coordinates = {"lat": 0, "lng": 0}
    if "loc" in gem and gem["loc"]:
        if isinstance(gem["loc"], dict):
            coordinates = {"lat": float(gem["loc"].get("lat", 0)), "lng": float(gem["loc"].get("lng", 0))}
    elif "coordinates" in gem:
        coordinates = gem["coordinates"]
    
    # Try to extract coordinates from map_url if available
    if coordinates["lat"] == 0 and coordinates["lng"] == 0:
        map_url = gem.get("map_url", "")
        if map_url:
            # Extract coordinates from Google Maps URL if present
            coords_match = re.search(r'[@!](-?\d+\.\d+),(-?\d+\.\d+)', map_url)
            if coords_match:
                coordinates = {"lat": float(coords_match.group(1)), "lng": float(coords_match.group(2))}
    
    # Try to extract analysis from the full response Markdown for this specific place
    place_name = gem.get("name", gem.get("placeName", ""))
    analysis = extract_analysis_from_markdown(place_name, full_response)
    
    # Generate photo URL (placeholder - in production, get from Google Places photos)
    photos = []
    if gem.get("map_url"):
        photos.append(gem["map_url"])
    photos.append("https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=800")
    
    return {
        "placeName": place_name or gem.get("placeName", "Unknown Place"),
        "address": gem.get("address", "Address not available"),
        "coordinates": coordinates,
        "rating": float(gem.get("rating", 0)),
        "reviewCount": int(gem.get("review_count", gem.get("reviewCount", gem.get("reviews", 0)))),
        "photos": photos,
        "analysis": analysis
    }


def extract_analysis_from_markdown(place_name: str, markdown_text: str) -> dict:
    """
    Extract analysis (whySpecial, bestTime, insiderTip) from Markdown response.
    The recommendation agent formats this in the Markdown.
    """
    analysis = {
        "whySpecial": "A hidden gem worth exploring",
        "bestTime": "Check local hours",
        "insiderTip": "Visit during off-peak hours for the best experience"
    }
    
    try:
        # Find the section for this specific place
        # Look for headers with the place name
        place_section_pattern = rf'###\s*\d+\.\s*{re.escape(place_name)}.*?(?=###|$)'
        place_section = re.search(place_section_pattern, markdown_text, re.DOTALL | re.IGNORECASE)
        
        if place_section:
            section_text = place_section.group(0)
            
            # Extract "Why it's special"
            why_match = re.search(r'\*\*Why it\'s a Hidden Gem:\*\*\s*(.+?)(?=\*\*|💡|📍|🗺️|$)', section_text, re.DOTALL)
            if why_match:
                analysis["whySpecial"] = why_match.group(1).strip()
            
            # Extract insider tip
            tip_match = re.search(r'💡\s*Insider Tip:\*\*\s*(.+?)(?=\*\*|📍|🗺️|$)', section_text, re.DOTALL)
            if tip_match:
                analysis["insiderTip"] = tip_match.group(1).strip()
            
            # Extract best time if mentioned
            time_match = re.search(r'(?:best time|best visit|ideal time):\s*([^\n]+)', section_text, re.IGNORECASE)
            if time_match:
                analysis["bestTime"] = time_match.group(1).strip()
    except Exception as e:
        print(f"[Backend] Could not extract analysis from Markdown: {e}")
    
    return analysis


def parse_markdown_response(markdown_text: str, query: str) -> dict:
    """
    Fallback parser: Extract structured data from Markdown response.
    The recommendation agent formats data as Markdown, so we extract what we can.
    """
    import json
    
    gems = []
    
    try:
        # Look for place names (usually in headers like ### 1. Place Name)
        place_matches = re.findall(r'###\s*\d+\.\s*([^\n(]+)', markdown_text)
        
        # Look for ratings (⭐ [Rating])
        rating_matches = re.findall(r'⭐\s*([\d.]+)', markdown_text)
        
        # Look for review counts (👤 [Count] reviews)
        review_matches = re.findall(r'👤\s*(\d+)\s*reviews?', markdown_text)
        
        # Look for addresses (📍 Location: [Address])
        address_matches = re.findall(r'📍\s*Location:\s*([^\n]+)', markdown_text)
        
        # Look for "Why it's special" sections
        why_special_matches = re.findall(r'\*\*Why it\'s a Hidden Gem:\*\*\s*([^\n]+(?:\n(?!\*\*|📍|🗺️|###)[^\n]+)*)', markdown_text, re.MULTILINE)
        
        # Look for insider tips
        tip_matches = re.findall(r'💡\s*Insider Tip:\*\*\s*([^\n]+(?:\n(?!\*\*|📍|🗺️|###)[^\n]+)*)', markdown_text, re.MULTILINE)
        
        # Extract data for each gem found
        max_gems = max(len(place_matches), len(address_matches), len(why_special_matches))
        
        for i in range(max_gems):
            place_name = place_matches[i] if i < len(place_matches) else f"Place {i+1}"
            rating = float(rating_matches[i]) if i < len(rating_matches) else 4.0
            review_count = int(review_matches[i]) if i < len(review_matches) else 0
            address = address_matches[i].strip() if i < len(address_matches) else "Address not available"
            why_special = why_special_matches[i].strip() if i < len(why_special_matches) else "A hidden gem worth exploring"
            tip = tip_matches[i].strip() if i < len(tip_matches) else "Visit during off-peak hours for the best experience"
            
            # Transform to match frontend format
            gem_dict = {
                "name": place_name.strip(),  # Will be transformed by transform_gem_format
                "rating": rating,
                "review_count": review_count,
                "address": address,
                "coordinates": {"lat": 0, "lng": 0},  # Would need geocoding
            }
            
            # Transform using the same function used for JSON gems
            transformed_gem = transform_gem_format(gem_dict, markdown_text)
            # Override analysis since we extracted it from Markdown
            transformed_gem["analysis"] = {
                "whySpecial": why_special,
                "bestTime": "Check local hours",
                "insiderTip": tip
            }
            
            gems.append(transformed_gem)
        
        if gems:
            print(f"[Backend] Extracted {len(gems)} gems from Markdown")
            return {"gems": gems}
        else:
            # Return empty if nothing found
            return {"gems": []}
            
    except Exception as e:
        print(f"[Backend] Error parsing Markdown: {e}")
        return {"gems": []}


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "I Got You API",
        "version": "1.0.0"
    }


@app.post("/api/discover")
async def discover_gems(request: DiscoveryRequest):
    """
    Discover hidden outdoor gems based on search query.

    Args:
        request: Discovery request with search query

    Returns:
        DiscoveryResponse with found hidden gems
    """
    print(f"\n{'='*60}")
    print(f"[Backend] Received search query: {request.searchQuery}")
    print(f"{'='*60}")

    try:
        import time
        start_time = time.time()

        print(f"[Backend] Running agent with query: {request.searchQuery}")

        # Run the agent
        response = await runner.run_debug(request.searchQuery)

        print(f"[Backend] Agent response received (length: {len(str(response))})")
        print(f"[Backend] Agent response preview: {str(response)[:200]}...")

        # Parse JSON response from recommendation agent
        parsed_data = parse_agent_response(str(response), request.searchQuery)

        # Calculate actual processing time
        processing_time = time.time() - start_time

        gems_count = len(parsed_data.get("gems", []))
        print(f"[Backend] Successfully parsed {gems_count} gems")
        print(f"[Backend] Processing time: {processing_time:.2f}s")

        # The recommendation agent now returns data in the correct format
        gems = parsed_data.get("gems", [])

        # Return the response with processing time and query
        return {
            "gems": gems,
            "processingTime": processing_time,
            "query": request.searchQuery
        }

    except Exception as e:
        print(f"[Backend] ERROR in discover_gems endpoint: {e}")
        import traceback
        traceback.print_exc()
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
    print("\n" + "="*60)
    print("🚀 Starting I Got You Backend API Server")
    print("="*60)
    print("📍 Server will run at: http://localhost:8000")
    print("📚 API Docs available at: http://localhost:8000/docs")
    print("🔄 Waiting for requests...")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
