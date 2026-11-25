from fastapi.testclient import TestClient
from mmppe.api.app import app
from mmppe.core.schemas import ExperimentConfig
from mmppe.runtime.engine import ExperimentRuntime

client=TestClient(app)

def test_multi_participant_package_loaded():
    data=client.get('/api/experiments').json()['demo_collaborative_rating']
    assert len(data['participants'])==3
    assert data['phases'][2]['advance_when']=='all_responses'

def test_runtime_multi_participant_responses_and_events():
    cfg=ExperimentConfig.model_validate(client.get('/api/experiments/demo_collaborative_rating').json())
    r=ExperimentRuntime(cfg); r.connect('P01'); r.connect('P02'); r.connect('P03'); r.start(); r.advance(); r.advance()
    for pid in ['P01','P02','P03']: r.submit_response(pid,4)
    assert len(r.responses)==3
    assert {x['participant_id'] for x in r.responses}=={'P01','P02','P03'}
    assert sum(e['event']=='PARTICIPANT_CONNECTED' for e in r.events)==3

def test_n_gt_5_is_valid():
    d={'id':'n7','name':'N7','participants':[{'id':f'P{i:02d}'} for i in range(1,8)],'phases':[{'id':'rest','type':'rest'}]}
    assert len(ExperimentConfig.model_validate(d).participants)==7

def test_device_independent_modalities():
    data=client.get('/api/experiments/demo_collaborative_rating').json()
    dumped=str(data).lower()
    assert 'emotiv' not in dumped and 'shimmer' not in dumped
    assert {s['modality'] for s in data['streams']}=={'EEG','AUDIO','VIDEO'}

def test_researcher_can_create_package_without_core_change(tmp_path):
    payload={'id':'ui_created_test','name':'UI Created Test','participants':[{'id':'P01'}], 'streams':[{'modality':'IMU','participant_id':'P01'}], 'phases':[{'id':'p1','type':'stimulus','stimulus':{'kind':'text','value':'hello'}}]}
    res=client.post('/api/experiments',json=payload); assert res.status_code==200
    assert client.get('/api/experiments/ui_created_test').status_code==200
    import shutil
    shutil.rmtree('experiments/ui_created_test', ignore_errors=True)
