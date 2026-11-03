import requests


class WeatherForecastTool:
    def __init__(self, api_key: str | None):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"

    def get_current_weather(self, place: str):
        if not self.api_key:
            return {}
        response = requests.get(
            f"{self.base_url}/weather",
            params={"q": place, "appid": self.api_key, "units": "metric"},
            timeout=12,
        )
        return response.json() if response.status_code == 200 else {}

    def get_forecast_weather(self, place: str):
        if not self.api_key:
            return {}
        response = requests.get(
            f"{self.base_url}/forecast",
            params={"q": place, "appid": self.api_key, "cnt": 10, "units": "metric"},
            timeout=12,
        )
        return response.json() if response.status_code == 200 else {}
