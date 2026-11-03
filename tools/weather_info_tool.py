import os
from typing import List

from dotenv import load_dotenv
from langchain.tools import tool

from utils.weather_info import WeatherForecastTool


class WeatherInfoTool:
    def __init__(self):
        load_dotenv()
        self.api_key = os.environ.get("OPENWEATHERMAP_API_KEY")
        self.weather_service = WeatherForecastTool(self.api_key) if self.api_key else None
        self.weather_tool_list = self._setup_tools()

    def _setup_tools(self) -> List:
        @tool
        def get_current_weather(city: str) -> str:
            """Get current weather for a city."""
            if self.weather_service is None:
                return "Weather data is unavailable because OPENWEATHERMAP_API_KEY is not configured on the backend."
            weather_data = self.weather_service.get_current_weather(city)
            if weather_data:
                temp = weather_data.get("main", {}).get("temp", "N/A")
                desc = weather_data.get("weather", [{}])[0].get("description", "N/A")
                return f"Current weather in {city}: {temp}°C, {desc}"
            return f"Could not fetch weather for {city}."

        @tool
        def get_weather_forecast(city: str) -> str:
            """Get weather forecast for a city."""
            if self.weather_service is None:
                return "Weather forecast is unavailable because OPENWEATHERMAP_API_KEY is not configured on the backend."
            forecast_data = self.weather_service.get_forecast_weather(city)
            if forecast_data and "list" in forecast_data:
                forecast_summary = []
                for item in forecast_data["list"]:
                    date = item["dt_txt"].split(" ")[0]
                    temp = item["main"]["temp"]
                    desc = item["weather"][0]["description"]
                    forecast_summary.append(f"{date}: {temp}°C, {desc}")
                return f"Weather forecast for {city}:\n" + "\n".join(forecast_summary)
            return f"Could not fetch forecast for {city}."

        return [get_current_weather, get_weather_forecast]
