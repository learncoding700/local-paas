def test_empty_image_name_rejected(client, auth_headers, mock_docker):
    r = client.post("/deploy", json={"image": ""}, headers=auth_headers)
    assert r.status_code in (400, 422)


def test_semicolon_injection_rejected(client, auth_headers, mock_docker):
    r = client.post("/deploy", json={"image": "nginx; rm -rf /"}, headers=auth_headers)
    assert r.status_code in (400, 422)


def test_path_traversal_rejected(client, auth_headers, mock_docker):
    r = client.post("/deploy", json={"image": "../../etc/passwd"}, headers=auth_headers)
    assert r.status_code in (400, 422)


def test_pipe_injection_rejected(client, auth_headers, mock_docker):
    r = client.post("/deploy", json={"image": "nginx | cat /etc/passwd"}, headers=auth_headers)
    assert r.status_code in (400, 422)


def test_extremely_long_image_name_rejected(client, auth_headers, mock_docker):
    r = client.post("/deploy", json={"image": "a" * 300}, headers=auth_headers)
    assert r.status_code in (400, 422)
