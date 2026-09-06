"""Tests for task bulk-control route registration."""

from __future__ import annotations

from nightshift.app.main import app


def test_bulk_task_control_routes_are_registered() -> None:
    paths = app.openapi()["paths"]

    assert "/api/v1/tasks/cancel-all" in paths
    assert "post" in paths["/api/v1/tasks/cancel-all"]
    assert "/api/v1/tasks/retry-all" in paths
    assert "post" in paths["/api/v1/tasks/retry-all"]
