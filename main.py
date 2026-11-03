"""FastAPI backend for AI Trip Planner with request-scoped Groq BYOK."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

from utils.model_loader import ModelLoader

load_dotenv()
logger = logging.getLogger("ai_trip_planner.api")

app = FastAPI(title="AI Trip Planner API", version="1.0.0")

# The Streamlit frontend calls this API server-to-server. Credentials are carried
# in request headers, not cookies, so credentialed wildcard CORS is unnecessary.
allowed_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "*").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Groq-API-Key"],
)


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=12000)

    @staticmethod
    def _clean_question(value: str) -> str:
        return value.strip()


def _clean_api_key(api_key: str | None) -> str:
    key = (api_key or "").strip()
    if not key:
        raise HTTPException(
            status_code=401,
            detail="A Groq API key is required. Enter and validate your key in the frontend.",
        )
    if "\r" in key or "\n" in key or len(key) > 512:
        raise HTTPException(status_code=400, detail="The supplied API key is malformed.")
    return key


def _provider_error_response(exc: Exception) -> tuple[int, str]:
    """Map provider failures to safe messages without reflecting secrets."""
    status = getattr(exc, "status_code", None)
    response = getattr(exc, "response", None)
    if status is None and response is not None:
        status = getattr(response, "status_code", None)

    if status in (401, 403):
        return 401, "Groq rejected this API key. Check the key and try again."
    if status == 429:
        return 429, "Groq rate limit or quota reached. Check your Groq account and retry."
    return 502, "Could not reach Groq. Check provider availability, model access, and try again."


def _build_agent(api_key: str):
    # Lazy import keeps API health/docs importable without loading the agent stack.
    from agent.agentic_workflow import GraphBuilder

    graph_builder = GraphBuilder(model_provider="groq", api_key=api_key)
    return graph_builder()


@app.get("/")
def home():
    return {
        "message": "AI Trip Planner API is running!",
        "docs": "/docs",
        "query_endpoint": "/query",
        "key_validation_endpoint": "/validate-key",
    }


@app.get("/ping")
def ping():
    return {"status": "pong"}


@app.post("/validate-key")
async def validate_groq_key(x_groq_api_key: str | None = Header(default=None, alias="X-Groq-API-Key")):
    """Validate a user's Groq key without storing or logging it."""
    api_key = _clean_api_key(x_groq_api_key)
    try:
        loader = ModelLoader(model_provider="groq", api_key=api_key)
        await asyncio.to_thread(loader.validate_api_key)
        return {"valid": True, "provider": "groq", "message": "Groq API key validated."}
    except ValueError as exc:
        # Only known local validation errors are returned; never echo the key.
        raise HTTPException(status_code=400, detail=str(exc)) from None
    except Exception as exc:
        status_code, safe_message = _provider_error_response(exc)
        logger.warning("Groq key validation failed (%s)", type(exc).__name__)
        raise HTTPException(status_code=status_code, detail=safe_message) from None


@app.post("/query")
async def query_travel_agent(
    query: QueryRequest,
    x_groq_api_key: str | None = Header(default=None, alias="X-Groq-API-Key"),
):
    """Run one agent request using the API key supplied for that request."""
    api_key = _clean_api_key(x_groq_api_key)
    question = query.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="Question cannot be empty.")

    try:
        react_app = _build_agent(api_key)
        messages = {"messages": [question]}
        output: Any = await asyncio.to_thread(react_app.invoke, messages)

        if isinstance(output, dict) and output.get("messages"):
            last_message = output["messages"][-1]
            final_output = getattr(last_message, "content", str(last_message))
        else:
            final_output = str(output)

        return {"answer": final_output}
    except Exception as exc:
        # Do not log exception text: provider exceptions can contain request details.
        logger.error("Travel planning request failed (%s)", type(exc).__name__)
        return JSONResponse(
            status_code=500,
            content={
                "error": "The travel-planning request failed. Check provider status and backend tool configuration, then retry."
            },
        )
