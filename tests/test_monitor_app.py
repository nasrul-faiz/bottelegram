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


def test_generated_links_can_be_saved_and_listed(tmp_path, monkeypatch):
    monkeypatch.setattr('monitor_app.LINKS_PATH', tmp_path / 'generated_links.json')
    client = app.test_client()

    response = client.post('/api/links', json={
        'title': 'Demo link',
        'link': 'https://example.com/share/123',
        'description': 'contoh share link'
    })

    assert response.status_code == 201
    payload = response.get_json()
    assert payload['title'] == 'Demo link'
    assert payload['link'] == 'https://example.com/share/123'

    list_response = client.get('/api/links')
    assert list_response.status_code == 200
    items = list_response.get_json()
    assert len(items) == 1
    assert items[0]['link'] == 'https://example.com/share/123'
