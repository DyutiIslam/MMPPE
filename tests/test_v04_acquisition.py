from mmppe.acquisition.mapping import AcquisitionPlan

def streams():
    return [
      {'uid':'eeg1','name':'AnyVendor EEG P01','modality':'EEG','channel_count':8,'nominal_srate':250.0},
      {'uid':'imu1','name':'Custom Motion','modality':'IMU','channel_count':6,'nominal_srate':100.0},
    ]

def test_device_independent_mapping_and_preflight():
    p=AcquisitionPlan('x',[{'modality':'EEG','participant_id':'P01','required':True}])
    rid=p.requirement_rows()[0]['requirement_id']; p.map(rid,'eeg1')
    out=p.preflight(streams()); assert out['ready']; assert out['summary']['passed']==1

def test_missing_required_stream_blocks_preflight():
    p=AcquisitionPlan('x',[{'modality':'EEG','participant_id':'P01','required':True}])
    assert not p.preflight(streams())['ready']

def test_disappeared_stream_blocks_preflight():
    p=AcquisitionPlan('x',[{'modality':'EEG','participant_id':'P01','required':True}])
    rid=p.requirement_rows()[0]['requirement_id']; p.map(rid,'eeg1')
    assert not p.preflight([])['ready']

def test_modality_mismatch_blocks_preflight():
    p=AcquisitionPlan('x',[{'modality':'EEG','participant_id':'P01','required':True}])
    rid=p.requirement_rows()[0]['requirement_id']; p.map(rid,'imu1')
    assert not p.preflight(streams())['ready']

def test_same_physical_stream_cannot_map_twice():
    p=AcquisitionPlan('x',[{'modality':'EEG','participant_id':'P01'},{'modality':'EEG','participant_id':'P02'}])
    a,b=[r['requirement_id'] for r in p.requirement_rows()]; p.map(a,'eeg1')
    try: p.map(b,'eeg1'); assert False
    except ValueError: pass
