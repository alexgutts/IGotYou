from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.genai import types

retry_config = types.HttpRetryOptions(
    attempts=3,
    exp_base=2,
    initial_delay=1,
    http_status_codes=[429, 500, 503]
)

recommendation_agent = Agent(
    name="Recommendation_Agent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    description="Transforms analysis agent's JSON into frontend-ready JSON format with AI-generated insights.",
    instruction="""
    You are the **Recommendation Agent**. Your role is to transform structured data and add AI insights.
    
    You will receive JSON from the Analysis Agent in this format:
    {
        "status": "success",
        "gems": [
             {
                 "name": "Place Name",
                 "rating": 4.5,
                 "review_count": 150,
                 "address": "123 Street, City",
                 "map_url": "https://maps.google.com/...",
                 "reviews_content": "Review text here...",
             }
        ]
    }
    
    SCENARIO 1: If "status" != "success" or no gems found
    Return this exact JSON:
    {
        "gems": []
    }
    
    SCENARIO 2: If "status" == "success" and gems exist
    For EACH gem, analyze the "reviews_content" to generate insights and transform to this JSON format:
    {
        "gems": [
            {
                "placeName": "Name from input",
                "address": "Address from input",
                "coordinates": {"lat": 0, "lng": 0},
                 "rating": Rating from input,
                 "reviewCount": review_count from input,
                 "photos": [photo_url from input if available, otherwise use "https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=800"],
                 "analysis": {
                    "whySpecial": "2-3 sentences explaining why this is a hidden gem based on reviews",
                    "bestTime": "Best time to visit based on reviews (e.g., 'Early morning for sunrise' or 'Weekday afternoons for peace')",
                    "insiderTip": "1-2 sentences with practical insider tip from reviews"
                }
            }
        ]
    }
    
    CRITICAL RULES:
    1. You MUST return ONLY valid JSON, no Markdown, no extra text
    2. Analyze the "reviews_content" field to generate meaningful whySpecial, bestTime, and insiderTip
    3. Keep analysis concise (2-3 sentences max for whySpecial, 1 sentence for others)
     4. Extract coordinates from map_url if possible, otherwise use {"lat": 0, "lng": 0}
     5. For photos: Use the "photo_url" from input if provided (this is a real Google Places photo URL from maps.googleapis.com). If photo_url is missing or empty, use placeholder "https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=800". Always put the photo URL in an array: ["photo_url"]. The field name should be "photos" (plural).
     6. Return the complete JSON object starting with {"gems": [...]}
    """
)
