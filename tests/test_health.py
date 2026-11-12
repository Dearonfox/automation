from app.api.health import health
from app.main import app


def test_health_check() -> None:
    assert health()["status"] == "ok"


def test_health_routes_are_registered() -> None:
    paths = {route.path for route in app.routes}
    assert "/health" in paths
    assert "/api/v1/health" in paths

