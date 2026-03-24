def test_deploy_returns_container_id_and_port(client, auth_headers, mock_docker):
    r = client.post("/deploy", json={"image": "nginx"}, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert "container_id" in body
    assert "host_port" in body
    assert "url" in body
    assert "status" in body


def test_deploy_saves_record_to_database(client, auth_headers, mock_docker):
    r = client.post("/deploy", json={"image": "nginx"}, headers=auth_headers)
    container_id = r.json()["container_id"]
    lst = client.get("/containers", headers=auth_headers)
    ids = [c["container_id"] for c in lst.json()]
    assert container_id in ids


def test_two_deploys_get_different_ports(client, auth_headers, mock_docker):
    r1 = client.post("/deploy", json={"image": "nginx"}, headers=auth_headers)
    r2 = client.post("/deploy", json={"image": "redis"}, headers=auth_headers)
    assert r1.status_code == 200 and r2.status_code == 200
    port1 = r1.json()["host_port"]
    port2 = r2.json()["host_port"]
    assert port1 != port2


def test_list_containers_returns_deployed_containers(client, auth_headers, mock_docker):
    client.post("/deploy", json={"image": "nginx"}, headers=auth_headers)
    client.post("/deploy", json={"image": "redis"}, headers=auth_headers)
    r = client.get("/containers", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()) >= 2


def test_stop_container_updates_status_to_stopped(client, auth_headers, mock_docker):
    r = client.post("/deploy", json={"image": "nginx"}, headers=auth_headers)
    container_id = r.json()["container_id"]
    stop = client.post("/stop", json={"container_id": container_id}, headers=auth_headers)
    assert stop.status_code == 200
    lst = client.get("/containers", headers=auth_headers)
    row = next(x for x in lst.json() if x["container_id"] == container_id)
    assert row["status"] == "stopped"


def test_remove_container_deletes_from_database(client, auth_headers, mock_docker):
    r = client.post("/deploy", json={"image": "nginx"}, headers=auth_headers)
    container_id = r.json()["container_id"]
    rm = client.request(
        "DELETE",
        "/remove",
        json={"container_id": container_id},
        headers=auth_headers,
    )
    assert rm.status_code == 200
    lst = client.get("/containers", headers=auth_headers)
    ids = [c["container_id"] for c in lst.json()]
    assert container_id not in ids


def test_stop_nonexistent_container_returns_404(client, auth_headers, mock_docker):
    r = client.post("/stop", json={"container_id": "doesnotexist999"}, headers=auth_headers)
    assert r.status_code == 404
