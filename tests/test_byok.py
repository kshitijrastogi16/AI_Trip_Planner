import sys
import types
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import main
from utils.model_loader import ModelLoader


class FakeResponse:
    def __init__(self, content="Trip plan"):
        self.content = content


def test_model_loader_requires_explicit_key_even_when_env_has_one(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "server-side-fallback-must-not-be-used")
    with pytest.raises(ValueError, match="Groq API key is required"):
        ModelLoader(api_key=None)


def test_model_loader_passes_explicit_key_to_groq_without_exposing_it(monkeypatch):
    secret = "test-groq-secret-not-for-logs"
    calls = {}

    class FakeChatGroq:
        def __init__(self, **kwargs):
            calls.update(kwargs)

        def invoke(self, prompt):
            calls["prompt"] = prompt
            return FakeResponse("OK")

    monkeypatch.setitem(
        sys.modules,
        "langchain_groq",
        types.SimpleNamespace(ChatGroq=FakeChatGroq),
    )

    loader = ModelLoader(api_key=secret)
    loader.validate_api_key()

    assert calls["api_key"] == secret
    assert calls["model"]
    assert "test-groq-secret" not in repr(loader)


def test_validate_endpoint_accepts_key_in_header_only(monkeypatch):
    calls = {}

    class FakeModelLoader:
        def __init__(self, model_provider, api_key):
            calls["provider"] = model_provider
            calls["api_key"] = api_key

        def validate_api_key(self):
            calls["validated"] = True

    monkeypatch.setattr(main, "ModelLoader", FakeModelLoader)
    client = TestClient(main.app)
    secret = "test-groq-header-secret"

    response = client.post(
        "/validate-key",
        headers={"X-Groq-API-Key": secret},
    )

    assert response.status_code == 200
    assert response.json()["valid"] is True
    assert calls == {"provider": "groq", "api_key": secret, "validated": True}
    assert secret not in response.text


def test_validate_endpoint_requires_key(monkeypatch):
    client = TestClient(main.app)
    response = client.post("/validate-key")
    assert response.status_code == 401
    assert "API key is required" in response.json()["detail"]


def test_validate_endpoint_does_not_echo_provider_exception_or_key(monkeypatch):
    secret = "test-secret-should-never-be-echoed"

    class FakeModelLoader:
        def __init__(self, model_provider, api_key):
            pass

        def validate_api_key(self):
            raise RuntimeError(f"provider error included {secret}")

    monkeypatch.setattr(main, "ModelLoader", FakeModelLoader)
    client = TestClient(main.app)
    response = client.post("/validate-key", headers={"X-Groq-API-Key": secret})

    assert response.status_code == 502
    assert secret not in response.text


def test_query_endpoint_passes_key_to_request_scoped_agent(monkeypatch):
    calls = {}

    class FakeGraph:
        def invoke(self, payload):
            calls["payload"] = payload
            return {"messages": [FakeResponse("A 3-day trip plan") ]}

    def fake_build_agent(api_key):
        calls["api_key"] = api_key
        return FakeGraph()

    monkeypatch.setattr(main, "_build_agent", fake_build_agent)
    client = TestClient(main.app)
    secret = "request-scoped-test-secret"

    response = client.post(
        "/query",
        json={"question": "Plan a trip to Jaipur"},
        headers={"X-Groq-API-Key": secret},
    )

    assert response.status_code == 200
    assert response.json()["answer"] == "A 3-day trip plan"
    assert calls["api_key"] == secret
    assert calls["payload"] == {"messages": ["Plan a trip to Jaipur"]}
    assert secret not in response.text


def test_query_endpoint_requires_key():
    client = TestClient(main.app)
    response = client.post("/query", json={"question": "Plan a trip to Jaipur"})
    assert response.status_code == 401


def test_query_request_rejects_empty_question():
    client = TestClient(main.app)
    response = client.post(
        "/query",
        json={"question": "   "},
        headers={"X-Groq-API-Key": "test-key"},
    )
    assert response.status_code == 422
