import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

pytest.importorskip("sqlmodel")

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_faros_routes_are_mounted():
    paths = {route.path for route in app.routes}
    expected_prefixes = [
        "/api/faros/health",
        "/api/faros/blueprints",
        "/api/faros/profiles",
        "/api/faros/capabilities",
        "/api/faros/runs",
    ]
    for prefix in expected_prefixes:
        assert any(path == prefix or path.startswith(prefix + "/") for path in paths), prefix


def test_faros_metadata_endpoints_return_assets():
    health = client.get("/api/faros/health")
    assert health.status_code == 200
    assert health.json()["runtime"] == "faros"

    blueprints = client.get("/api/faros/blueprints")
    assert blueprints.status_code == 200
    blueprint = next(item for item in blueprints.json()["blueprints"] if item["id"] == "ml_paper")
    assert len(blueprint["workflow"]) == 4

    profiles = client.get("/api/faros/profiles")
    assert profiles.status_code == 200
    assert any(item["id"] == "faros_llm" for item in profiles.json()["profiles"])


def test_faros_plan_run_can_be_created_without_provider_execution():
    response = client.post(
        "/api/faros/runs",
        json={
            "blueprintId": "ml_paper",
            "profileId": "faros_llm",
            "executionMode": "plan",
            "inputs": {
                "seedQuery": "Optimize CPU usage in LLM workflows",
                "paperType": "system",
                "targetVenue": "generic"
            }
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "planned"
    assert payload["blueprint_id"] == "ml_paper"
    assert payload["profile_id"] == "faros_llm"
    assert len(payload["steps"]) == 4
