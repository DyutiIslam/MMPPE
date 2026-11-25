from fastapi.testclient import TestClient
from mmppe.api.app import app

def test_researcher_ui_loads():
    c=TestClient(app)
    r=c.get('/')
    assert r.status_code == 200
    assert 'Research dashboard' in r.text
    assert 'Design a Study' in r.text
    assert 'Study Library' in r.text
    assert 'MMPPE' in r.text

def test_favicon_does_not_404():
    assert TestClient(app).get('/favicon.ico').status_code == 204
