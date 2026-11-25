from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Any, Dict, List, Optional
from uuid import uuid4
from pathlib import Path
import json, os
from mmppe.core.schemas import ExperimentConfig, PhaseConfig

def utc_now(): return datetime.now(timezone.utc).isoformat()

@dataclass
class ExperimentRuntime:
    config: ExperimentConfig
    runtime_id: str = field(default_factory=lambda: uuid4().hex)
    status: str="ready"; repetition_index:int=0; phase_index:int=-1
    paused: bool=False
    started_at:Optional[str]=None; completed_at:Optional[str]=None
    responses:List[Dict[str,Any]]=field(default_factory=list); events:List[Dict[str,Any]]=field(default_factory=list)
    connected:Dict[str,bool]=field(default_factory=dict)

    def __post_init__(self): self.connected={p.id:False for p in self.config.participants}
    @property
    def current_phase(self)->Optional[PhaseConfig]:
        return self.config.phases[self.phase_index] if 0<=self.phase_index<len(self.config.phases) else None
    def active_participants(self):
        p=self.current_phase
        return p.participants if p and p.participants is not None else [x.id for x in self.config.participants]
    def _persist(self):
        folder=Path(__file__).resolve().parents[2]/"data"/"sessions"
        folder.mkdir(parents=True,exist_ok=True)
        path=folder/(self.runtime_id+".json")
        tmp=folder/(self.runtime_id+".json.tmp")
        data={"format":"mmppe-session-v1","demo_mode":True,"participant_inputs":"demonstration_browser_entries","sensor_data_collected":False,"experiment":self.config.model_dump(),"snapshot":self.snapshot(),"events":self.events,"responses":self.responses}
        tmp.write_text(json.dumps(data,indent=2,default=str),encoding="utf-8")
        os.replace(tmp,path)
    def _event(self,event_type,**payload):
        e={"event":event_type,"timestamp_utc":utc_now(),"runtime_id":self.runtime_id,"experiment_id":self.config.id,"repetition":self.repetition_index+1 if self.status!="ready" else 0,"phase_id":self.current_phase.id if self.current_phase else None,**payload}; self.events.append(e); self._persist(); return e
    def connect(self,participant_id):
        if participant_id not in self.connected: raise ValueError(f"Unknown participant: {participant_id}")
        self.connected[participant_id]=True; self._event("PARTICIPANT_CONNECTED",participant_id=participant_id); return self.snapshot()
    def disconnect(self,participant_id):
        if participant_id not in self.connected: raise ValueError(f"Unknown participant: {participant_id}")
        self.connected[participant_id]=False; self._event("PARTICIPANT_DISCONNECTED",participant_id=participant_id); return self.snapshot()
    def start(self):
        if self.status!="ready": raise ValueError("Runtime has already been started.")
        self.status="running"; self.started_at=utc_now(); self.repetition_index=0; self.phase_index=0
        self._event("SESSION_START"); self._enter_phase(); return self.snapshot()
    def _enter_phase(self):
        self._event("PHASE_START",active_participants=self.active_participants())
        if self.current_phase and self.current_phase.stimulus: self._event("STIMULUS_ONSET",active_participants=self.active_participants())
    def submit_response(self,participant_id,value):
        p=self.current_phase
        if self.status!="running" or self.paused or not p: raise ValueError("No active phase is accepting a response.")
        if participant_id not in {x.id for x in self.config.participants}: raise ValueError(f"Unknown participant: {participant_id}")
        if participant_id not in self.active_participants(): raise ValueError(f"Participant '{participant_id}' is not active in this phase.")
        if not p.response: raise ValueError(f"Phase '{p.id}' does not define a response.")
        if any(r["participant_id"]==participant_id and r["phase_id"]==p.id and r["repetition"]==self.repetition_index+1 for r in self.responses): raise ValueError("Response already recorded for this participant in this phase.")
        r={"participant_id":participant_id,"phase_id":p.id,"repetition":self.repetition_index+1,"value":value,"timestamp_utc":utc_now()}; self.responses.append(r); self._event("RESPONSE",participant_id=participant_id); return r
    def pause(self):
        if self.status!="running" or self.paused: raise ValueError("Cannot pause this session.")
        self.paused=True; self._event("SESSION_PAUSED"); return self.snapshot()
    def resume(self):
        if self.status!="running" or not self.paused: raise ValueError("Session is not paused.")
        self.paused=False; self._event("SESSION_RESUMED"); return self.snapshot()
    def advance(self):
        if self.status!="running" or self.paused: raise ValueError("Runtime is not running or is paused.")
        self._event("PHASE_END")
        if self.phase_index+1<len(self.config.phases): self.phase_index+=1
        elif self.repetition_index+1<self.config.repetitions: self.repetition_index+=1; self.phase_index=0
        else:
            self.status="completed"; self.completed_at=utc_now(); self.phase_index=len(self.config.phases); self._event("SESSION_END"); return self.snapshot()
        self._enter_phase(); return self.snapshot()
    def snapshot(self):
        p=self.current_phase
        return {"runtime_id":self.runtime_id,"experiment_id":self.config.id,"experiment_name":self.config.name,"status":self.status,"paused":self.paused,"repetition":self.repetition_index+1 if self.status!="ready" else 0,"repetitions_total":self.config.repetitions,"phase_index":self.phase_index,"phase_count":len(self.config.phases),"phase":p.model_dump() if p else None,"active_participants":self.active_participants() if p else [],"participants":[x.model_dump()|{"connected":self.connected[x.id]} for x in self.config.participants],"streams":[s.model_dump() for s in self.config.streams],"started_at":self.started_at,"completed_at":self.completed_at,"response_count":len(self.responses),"event_count":len(self.events)}

class RuntimeManager:
    def __init__(self): self._items={}; self._lock=RLock()
    def create(self,config):
        r=ExperimentRuntime(config=config)
        with self._lock:self._items[r.runtime_id]=r
        r._persist()
        return r
    def get(self,runtime_id):
        with self._lock:
            if runtime_id not in self._items: raise KeyError(runtime_id)
            return self._items[runtime_id]
