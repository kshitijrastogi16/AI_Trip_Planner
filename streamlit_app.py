from __future__ import annotations

import datetime
import os
from urllib.parse import urlparse

import requests
import streamlit as st

BASE_URL = os.getenv("API_BASE_URL", "https://ai-trip-planner-api-ltsk.onrender.com").rstrip("/")


def _is_secure_api_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme == "https":
        return True
    return parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1"}


def _invalidate_key_validation() -> None:
    st.session_state["groq_key_validated"] = False


def _clear_key() -> None:
    st.session_state["groq_api_key"] = ""
    st.session_state["groq_key_validated"] = False


def _api_headers(api_key: str) -> dict[str, str]:
    return {"X-Groq-API-Key": api_key}


st.set_page_config(
    page_title="🌍 Travel Planner Agentic Application",
    page_icon="🌍",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.title("🌍 Travel Planner Agentic Application")
st.caption("Plan trips with your own Groq API key. Your key is used for your requests and is not saved by this app.")

st.session_state.setdefault("messages", [])
st.session_state.setdefault("groq_key_validated", False)
st.session_state.setdefault("groq_api_key", "")

with st.sidebar:
    st.header("Bring Your Own Key")
    st.caption("Enter your Groq API key to unlock trip planning. The key is kept in this Streamlit session only; it is not written to a file or browser local storage.")
    st.text_input(
        "Groq API key",
        type="password",
        key="groq_api_key",
        placeholder="gsk_…",
        help="Create a key in your Groq account. Never share it with anyone.",
        on_change=_invalidate_key_validation,
    )

    if st.button("Validate API key", use_container_width=True):
        key = st.session_state.get("groq_api_key", "").strip()
        if not key:
            st.error("Enter your Groq API key first.")
        elif not _is_secure_api_url(BASE_URL):
            st.error("The API URL must use HTTPS. HTTP is allowed only for localhost development.")
        else:
            try:
                with st.spinner("Validating your Groq key..."):
                    response = requests.post(
                        f"{BASE_URL}/validate-key",
                        headers=_api_headers(key),
                        timeout=(10, 45),
                        allow_redirects=False,
                    )
                if response.ok and response.json().get("valid") is True:
                    st.session_state["groq_key_validated"] = True
                    st.success("Groq API key validated. Trip planning is unlocked.")
                else:
                    st.session_state["groq_key_validated"] = False
                    detail = response.json().get("detail", "Key validation failed.")
                    st.error(detail)
            except requests.RequestException:
                st.session_state["groq_key_validated"] = False
                st.error("Could not reach the trip-planner API. Check the backend URL and service status.")
            except ValueError:
                st.session_state["groq_key_validated"] = False
                st.error("The API returned an unexpected validation response.")

    st.button("Clear key", on_click=_clear_key, use_container_width=True)

    if st.session_state.get("groq_key_validated"):
        st.success("Key status: validated for this session")
    else:
        st.warning("Key status: locked — validate your key to continue")

if not _is_secure_api_url(BASE_URL):
    st.error("API_BASE_URL must be HTTPS except for localhost development.")

st.header("How can I help you plan a trip?")
st.write("Tell me your destination, trip duration, interests, or budget.")

with st.form(key="query_form", clear_on_submit=True):
    user_input = st.text_input(
        "Your trip request",
        placeholder="e.g. Plan a 5-day trip to New Delhi within ₹25,000.",
    )
    submit_button = st.form_submit_button(
        "Generate trip plan",
        disabled=not st.session_state.get("groq_key_validated", False),
    )

if submit_button and user_input.strip():
    if not st.session_state.get("groq_key_validated"):
        st.error("Validate your Groq API key before generating a trip plan.")
        st.stop()

    key = st.session_state.get("groq_api_key", "").strip()
    try:
        with st.spinner("Planning your trip..."):
            response = requests.post(
                f"{BASE_URL}/query",
                json={"question": user_input.strip()},
                headers=_api_headers(key),
                timeout=(10, 180),
                allow_redirects=False,
            )

        if response.ok:
            answer = response.json().get("answer", "No answer returned.")
            generated_at = datetime.datetime.now().strftime("%Y-%m-%d at %H:%M")
            st.markdown(
                f"# 🌍 AI Travel Plan\n\n"
                f"**Generated:** {generated_at}\n\n"
                f"---\n\n{answer}\n\n---\n\n"
                "*This travel plan was generated by AI. Please verify prices, operating hours, "
                "and travel requirements before your trip.*"
            )
        else:
            try:
                error_message = response.json().get("detail") or response.json().get("error")
            except ValueError:
                error_message = None
            st.error(error_message or f"Trip planning failed (HTTP {response.status_code}).")
    except requests.Timeout:
        st.error("The trip-planning request timed out. Please retry.")
    except requests.RequestException:
        st.error("Could not reach the trip-planner API. Check the backend URL and service status.")
