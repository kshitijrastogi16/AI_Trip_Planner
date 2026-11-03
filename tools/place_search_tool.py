import os
from typing import List

from dotenv import load_dotenv
from langchain.tools import tool

from utils.place_info_search import GooglePlaceSearchTool, TavilyPlaceSearchTool


class PlaceSearchTool:
    """Place-search tools with optional backend-managed provider credentials.

    Groq BYOK is independent from these search providers. If neither Google
    Places nor Tavily is configured on the API service, the agent still starts
    and these tools return a clear unavailable message when called.
    """

    def __init__(self, api_key: str | None = None):
        load_dotenv()
        google_key = api_key or os.getenv("GPLACES_API_KEY")
        self.google_places_search = GooglePlaceSearchTool(google_key) if google_key else None
        self.tavily_search = TavilyPlaceSearchTool()
        self.place_search_tool_list = self._setup_tools()

    def _search(self, google_method: str, tavily_method: str, location: str, label: str) -> str:
        if not location:
            return "Please provide a city or location."

        if self.google_places_search is not None:
            try:
                result = getattr(self.google_places_search, google_method)(location)
                if result:
                    return f"{label} in {location} (Google Places): {result}"
            except Exception:
                # Fall through to Tavily without exposing provider errors or keys.
                pass

        try:
            result = getattr(self.tavily_search, tavily_method)(location)
            if result:
                return f"{label} in {location} (web search): {result}"
        except Exception:
            pass

        return (
            f"Live {label.lower()} search is unavailable. Configure GPLACES_API_KEY "
            "or TAVILY_API_KEY on the backend service."
        )

    def _setup_tools(self) -> List:
        @tool
        def search_attractions(location: str = None, city: str = None, place: str = None) -> str:
            """Search tourist attractions. Supply the destination using location, city, or place."""
            destination = location or city or place
            return self._search("google_search_attractions", "tavily_search_attractions", destination, "Attractions")

        @tool
        def search_restaurants(location: str) -> str:
            """Search for restaurants and eateries in a specified location."""
            return self._search("google_search_restaurants", "tavily_search_restaurants", location, "Restaurants")

        @tool
        def search_activities(location: str) -> str:
            """Search for popular activities in a specified location."""
            return self._search("google_search_activity", "tavily_search_activity", location, "Activities")

        @tool
        def search_transportation(location: str) -> str:
            """Search for transportation options in a specified location."""
            return self._search("google_search_transportation", "tavily_search_transportation", location, "Transportation")

        return [search_attractions, search_restaurants, search_activities, search_transportation]
