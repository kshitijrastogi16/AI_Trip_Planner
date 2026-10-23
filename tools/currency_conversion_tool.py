
import os
from typing import List

import requests
from dotenv import load_dotenv
from langchain.tools import tool


class CurrencyConverterTool:
    def __init__(self):
        load_dotenv()

        self.api_key = os.getenv("EXCHANGE_RATE_API_KEY")
        self.currency_converter_tool_list = self._setup_tools()

    def _setup_tools(self) -> List:
        """Set up currency conversion tools."""

        @tool
        def convert_currency(
            amount: float,
            from_currency: str,
            to_currency: str,
        ) -> str:
            """Convert an amount between two currencies using
            the ExchangeRate-API service.

            Args:
                amount: Amount to convert.
                from_currency: Source currency code, e.g. USD.
                to_currency: Target currency code, e.g. INR.
            """
            if not self.api_key:
                return (
                    "Currency conversion unavailable: "
                    "EXCHANGE_RATE_API_KEY is missing from .env."
                )

            source = from_currency.strip().upper()
            target = to_currency.strip().upper()

            if amount < 0:
                return "Error: Amount cannot be negative."

            url = (
                "https://v6.exchangerate-api.com/v6/"
                f"{self.api_key}/pair/{source}/{target}/{amount}"
            )

            try:
                response = requests.get(url, timeout=15)
                response.raise_for_status()
                data = response.json()

                if data.get("result") != "success":
                    return (
                        "Currency conversion failed: "
                        f"{data.get('error-type', 'Unknown API error')}"
                    )

                converted = data["conversion_result"]
                rate = data["conversion_rate"]

                return (
                    f"{amount:.2f} {source} = "
                    f"{converted:.2f} {target} "
                    f"(exchange rate: 1 {source} = "
                    f"{rate} {target})"
                )

            except requests.RequestException as exc:
                return f"Currency API request failed: {exc}"
            except (KeyError, ValueError) as exc:
                return f"Could not process currency API response: {exc}"

        return [convert_currency]
