from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from mmppe.core.config import load_experiment_config
from mmppe.runtime.engine import ExperimentRuntime
from mmppe.api.app import app

ROOT = Path(__file__).resolve().parents[1]

def demo_config():
    return load_experiment_config(ROOT / "experiments" / "demo_single_participant" / "experiment.json")

def test_generic_runtime_completes_n1_demo():
    runtime = ExperimentRuntime(demo_config())
    state = runtime.start()
    assert state["phase"]["id"] == "baseline"
    runtime.advance()
    assert runtime.current_phase.id == "stimulus"
    runtime.advance()
    assert runtime.current_phase.id == "response"
    runtime.submit_response("P01", 4)
    state = runtime.advance()
    assert state["status"] == "completed"
    assert [e["event"] for e in runtime.events].count("SESSION_START") == 1
    assert [e["event"] for e in runtime.events].count("SESSION_END") == 1
    assert runtime.responses[0]["value"] == 4

def test_response_rejected_on_nonresponse_phase():
    runtime = ExperimentRuntime(demo_config())
    runtime.start()
    with pytest.raises(ValueError): runtime.submit_response("P01", 3)

def test_runtime_api_flow():
    c = TestClient(app)
    created = c.post('/api/runtime/demo_single_participant').json()
    rid = created['runtime_id']
    assert c.post(f'/api/runtime/{rid}/start').status_code == 200
    assert c.post(f'/api/runtime/{rid}/advance').json()['phase']['id'] == 'stimulus'
    assert c.post(f'/api/runtime/{rid}/advance').json()['phase']['id'] == 'response'
    assert c.post(f'/api/runtime/{rid}/response', json={'participant_id':'P01','value':5}).status_code == 200
    assert c.post(f'/api/runtime/{rid}/advance').json()['status'] == 'completed'
