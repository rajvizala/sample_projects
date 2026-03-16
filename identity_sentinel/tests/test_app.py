import os
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

TEST_DB_PATH = Path(tempfile.gettempdir()) / 'identity_sentinel_test.db'


def build_client():
    os.environ['IDENTITY_SENTINEL_DB_PATH'] = str(TEST_DB_PATH)
    from app.main import app, startup
    startup()
    return TestClient(app)


def test_dashboard_contains_seed_metrics():
    client = build_client()
    response = client.get('/api/dashboard')
    assert response.status_code == 200
    payload = response.json()
    assert payload['metrics']['total_signals'] >= 7
    assert payload['alerts']


def test_high_risk_signal_scores_critical_or_high():
    client = build_client()
    response = client.post(
        '/api/signals',
        json={
            'channel': 'voice',
            'sender': 'Unknown CFO',
            'content': 'Urgent wire request. Send OTP now to avoid account suspension.',
            'country': 'RU',
            'hour': 2,
            'amount': 950,
            'new_device': True,
            'new_ip': True,
            'ai_voice_flag': True,
        },
    )
    assert response.status_code == 200
    severity = response.json()['alert']['severity']
    assert severity in {'high', 'critical'}
