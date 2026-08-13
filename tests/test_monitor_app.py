from monitor_app import app


def test_health_endpoint():
    client = app.test_client()
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert 'status' in data
    assert 'bot' in data


def test_index_page_renders():
    client = app.test_client()
    response = client.get('/')
    assert response.status_code == 200
    assert b'Bot Monitor' in response.data
