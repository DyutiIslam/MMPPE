from fastapi.testclient import TestClient
from mmppe.api.app import app

def test_studio_routes_and_library():
 c=TestClient(app)
 for url in ('/','/studio','/studio.css','/studio.js','/showcase','/observer','/p1'):
  assert c.get(url).status_code==200
 studies=c.get('/api/experiments').json()
 assert 'resting_state_protocol' in studies
 assert 'stimulus_response_study' in studies
 assert 'group_decision_protocol' in studies

def test_study_builder_api_roundtrip():
 c=TestClient(app)
 cfg={'id':'test_studio_roundtrip','name':'Test Builder Study','participants':[{'id':'P01'}],'phases':[{'id':'baseline','type':'baseline','title':'Rest','duration_sec':30},{'id':'response','type':'response','title':'Rating','response':{'kind':'scale','min':1,'max':5}}],'streams':[{'modality':'EEG','required':False}]}
 assert c.post('/api/experiments',json=cfg).status_code==200
 assert c.get('/api/experiments/test_studio_roundtrip').json()['name']=='Test Builder Study'
 run=c.post('/api/showcase/select/test_studio_roundtrip')
 assert run.status_code==200
 rid=run.json()['runtime_id']
 assert c.post(f'/api/runtime/{rid}/start').status_code==200
 assert c.post(f'/api/runtime/{rid}/advance').status_code==200
 assert c.post(f'/api/runtime/{rid}/response',json={'participant_id':'P01','value':3}).status_code==200
 assert c.get(f'/api/runtime/{rid}/export').status_code==200
