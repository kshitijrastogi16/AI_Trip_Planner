from typing import List
from langchain.tools import tool

from utils.place_info_search import GooglePlaceSearchTool, TavilyPlaceSearchTool


class PlaceSearchTool:
    def __init__(self, api_key: str = None):
        import os
        from dotenv import load_dotenv
        load_dotenv()
        api_key = api_key or os.getenv("GPLACES_API_KEY")
        if not api_key:
            raise ValueError(
                "Missing GPLACES_API_KEY. Add it to your .env file."
            )
        self.google_places_search = GooglePlaceSearchTool(api_key)
        self.tavily_search = TavilyPlaceSearchTool()
        self.place_search_tool_list = self._setup_tools()

    def _setup_tools(self) -> List:
        """Set up all place-search tools."""

        @tool
        def search_attractions(location: str = None, city: str = None, place: str = None) -> str:
            """Search tourist attractions. Supply the destination using location, city, or place."""
            place = location or city or place
            if not place:
                return "Please provide a city or location."
            try:
                result = self.google_places_search.google_search_attractions(place)
                if result:
                    return f"Following are the attractions of {place} as suggested by Google: {result}"
            except Exception as e:
                tavily_result = self.tavily_search.tavily_search_attractions(place)
                return (
                    f"Google could not find the details due to {e}. "
                    f"Following are the attractions of {place}: {tavily_result}"
                )
            return f"No attractions found for {place}."

        @tool
        def search_restaurants(location: str) -> str:
            """Search for restaurants and eateries in a specified location. Provide the city or place as location."""
            place = location
            try:
                result = self.google_places_search.google_search_restaurants(place)
                if result:
                    return f"Following are the restaurants of {place} as suggested by Google: {result}"
            except Exception as e:
                tavily_result = self.tavily_search.tavily_search_restaurants(place)
                return (
                    f"Google could not find the details due to {e}. "
                    f"Following are the restaurants of {place}: {tavily_result}"
                )
            return f"No restaurants found for {place}."

        @tool
        def search_activities(location: str) -> str:
            """Search for popular activities in a specified location. Provide the city or place as location."""
            place = location
            try:
                result = self.google_places_search.google_search_activity(place)
                if result:
                    return f"Following are the activities in and around {place} as suggested by Google: {result}"
            except Exception as e:
                tavily_result = self.tavily_search.tavily_search_activity(place)
                return (
                    f"Google could not find the details due to {e}. "
                    f"Following are the activities of {place}: {tavily_result}"
                )
            return f"No activities found for {place}."

        @tool
        def search_transportation(location: str) -> str:
            """Search for available transportation options in a specified location. Provide the city or place as location."""
            place = location
            try:
                result = self.google_places_search.google_search_transportation(place)
                if result:
                    return f"Following are the modes of transportation available in {place} as suggested by Google: {result}"
            except Exception as e:
                tavily_result = self.tavily_search.tavily_search_transportation(place)
                return (
                    f"Google could not find the details due to {e}. "
                    f"Following are the modes of transportation available in {place}: {tavily_result}"
                )
            return f"No transportation information found for {place}."

        return [
            search_attractions,
            search_restaurants,
            search_activities,
            search_transportation,
        ]
