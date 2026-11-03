# AI Trip Planner

An agentic travel-planning application with a Streamlit frontend and FastAPI/LangGraph backend. The LLM provider uses **Bring Your Own Key (BYOK)**: each user supplies their own Groq API key through the frontend.

## BYOK request flow

1. The user enters a Groq API key in the Streamlit sidebar.
2. The frontend sends the key to `POST /validate-key` in the `X-Groq-API-Key` HTTP header.
3. The API constructs a Groq client with that explicit key and sends a minimal validation request.
4. After validation, each `/query` request carries the same header over HTTPS.
5. The backend creates a fresh agent graph for that request. It does not read a shared `GROQ_API_KEY` environment variable, persist the key, or include the key in application responses/log messages.
6. The frontend keeps the key only in Streamlit session state. Clearing the key or starting a new browser session requires validation again.

**Security notes:** use HTTPS for remote API URLs. Do not put user keys in query parameters, JSON request bodies, source files, `.env` files, logs, or analytics. The FastAPI service receives the key in memory to authenticate provider requests; as with any server-side BYOK design, the API host must be trusted.

## Run locally

Use Python 3.10 or newer.

```bash
python -m venv .venv
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
# Git Bash: source .venv/Scripts/activate
pip install -r requirements.txt
```

For local tests, install the development dependencies too:

```bash
pip install -r requirements-dev.txt
```

Copy `.env.example` to `.env` only for backend-managed optional integrations and the frontend API URL. **Do not add a shared `GROQ_API_KEY`**; users enter that key in the UI.

Start the FastAPI backend:

```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

In another terminal, set the frontend API URL and run Streamlit:

```bash
# Git Bash
export API_BASE_URL=http://127.0.0.1:8000
streamlit run streamlit_app.py
```

For a deployed frontend, set `API_BASE_URL` to the HTTPS URL of the deployed FastAPI backend.

## Deploying the split frontend/backend

This repository contains two deployable processes:

- **FastAPI backend:** deploy the repository root with build command `pip install -r requirements.txt` and start command `uvicorn main:app --host 0.0.0.0 --port $PORT`. Set optional backend integration keys (`GPLACES_API_KEY`, `TAVILY_API_KEY`, `OPENWEATHERMAP_API_KEY`, and `EXCHANGE_RATE_API_KEY`) only for tools you enable. Do not set a shared `GROQ_API_KEY` for BYOK mode.
- **Streamlit frontend:** deploy `streamlit_app.py` with `streamlit run streamlit_app.py`. Set `API_BASE_URL` to the backend's HTTPS URL in the frontend service configuration.

Deploy the backend changes and the frontend changes together. A frontend connected to an older backend will not have `/validate-key` and will not accept the new BYOK request header.

## API endpoints

- `GET /` — service information
- `GET /ping` — health check
- `POST /validate-key` — validates the caller's Groq key from `X-Groq-API-Key`
- `POST /query` — generates a trip plan using the caller's key

Example (use a shell environment variable rather than writing the key into shell history where possible):

```bash
curl -X POST "$API_BASE_URL/validate-key" \
  -H "X-Groq-API-Key: $GROQ_API_KEY"

curl -X POST "$API_BASE_URL/query" \
  -H "Content-Type: application/json" \
  -H "X-Groq-API-Key: $GROQ_API_KEY" \
  -d '{"question":"Plan a 3-day trip to Jaipur"}'
```

## Optional backend-managed tools

The Groq LLM key is user-supplied. Other integrations are separate services and, in this version, use backend-managed environment variables:

- `GPLACES_API_KEY` — Google Places; optional if Tavily search is configured
- `TAVILY_API_KEY` — Tavily fallback for place discovery; optional
- `OPENWEATHERMAP_API_KEY` — weather; optional
- `EXCHANGE_RATE_API_KEY` — currency conversion; optional
- `CORS_ALLOWED_ORIGINS` — optional comma-separated CORS origins (default `*`; credentials are disabled)

If optional keys are absent, those specific tools return an unavailable message; they do not prevent agent initialization. Configure only keys for services you actually use.

## Tests

```bash
python -m pytest -q
```

The BYOK tests mock the provider and agent so no real Groq key or billable request is needed.
