import os
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

TEST_DB_PATH = Path(tempfile.gettempdir()) / 'family_os_test.db'


def build_client():
    os.environ['FAMILY_OS_DB_PATH'] = str(TEST_DB_PATH)
    from app.main import app, startup
    startup()
    return TestClient(app)


def test_dashboard_renders_seeded_data():
    client = build_client()
    response = client.get('/api/dashboard')
    assert response.status_code == 200
    payload = response.json()
    assert len(payload['people']) == 4
    assert payload['digest']
    assert payload['suggestions']


def test_update_can_create_memory():
    client = build_client()
    response = client.post(
        '/api/updates',
        json={
            'person_id': 1,
            'category': 'family',
            'mood': 'excited',
            'text': 'We won the neighborhood cooking contest and should celebrate tonight.',
        },
    )
    assert response.status_code == 200
    dashboard = response.json()['dashboard']
    titles = [memory['title'] for memory in dashboard['memories']]
    assert any(title.startswith('Milestone:') for title in titles)
