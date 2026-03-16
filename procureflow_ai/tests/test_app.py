import os
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

TEST_DB_PATH = Path(tempfile.gettempdir()) / 'procureflow_ai_test.db'


def build_client():
    os.environ['PROCUREFLOW_DB_PATH'] = str(TEST_DB_PATH)
    from app.main import app, startup
    startup()
    return TestClient(app)


def test_dashboard_has_recommendations_and_forecasts():
    client = build_client()
    response = client.get('/api/dashboard')
    assert response.status_code == 200
    payload = response.json()
    assert payload['forecasts']
    assert payload['recommendations']


def test_requisition_creation_returns_updated_dashboard():
    client = build_client()
    response = client.post(
        '/api/requisitions',
        json={
            'title': 'Replacement power modules',
            'category': 'electronics',
            'quantity': 90,
            'needed_by': '2026-04-10',
            'priority': 'high',
            'required_certifications': ['ISO9001'],
        },
    )
    assert response.status_code == 200
    assert any(req['title'] == 'Replacement power modules' for req in response.json()['dashboard']['requisitions'])
