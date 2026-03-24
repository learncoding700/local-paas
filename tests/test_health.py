def test_root_returns_200(client):
    r = client.get("/")
    assert r.status_code == 200


def test_health_returns_200(client):
    r = client.get("/health")
    assert r.status_code == 200


def test_health_has_required_fields(client):
    r = client.get("/health")
    body = r.json()
    assert "api" in body
    assert "database" in body
    assert "docker" in body
    assert "status" in body


def test_stats_returns_200(client):
    r = client.get("/stats")
    assert r.status_code == 200
    body = r.json()
    assert "running" in body
    assert "stopped" in body
    assert "total_deployments" in body


def test_metrics_endpoint_returns_200(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "api_requests_total" in r.text
