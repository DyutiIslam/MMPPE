from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

@dataclass
class AcquisitionPlan:
    experiment_id: str
    requirements: List[Dict[str, Any]]
    mappings: Dict[str, str] = field(default_factory=dict)

    @staticmethod
    def key(req: Dict[str, Any], index: int) -> str:
        return f"R{index:03d}:{req.get('participant_id') or 'SESSION'}:{req.get('modality','OTHER')}"

    def requirement_rows(self) -> List[Dict[str, Any]]:
        rows=[]
        for i, req in enumerate(self.requirements, 1):
            row=dict(req); row['requirement_id']=self.key(req,i); row['mapped_uid']=self.mappings.get(row['requirement_id'])
            rows.append(row)
        return rows

    def map(self, requirement_id: str, stream_uid: str) -> None:
        if requirement_id not in {r['requirement_id'] for r in self.requirement_rows()}:
            raise ValueError('Unknown acquisition requirement.')
        if not stream_uid: raise ValueError('stream_uid is required.')
        # A physical LSL stream may only satisfy one requirement unless future explicit fan-out is supported.
        for rid, uid in self.mappings.items():
            if uid == stream_uid and rid != requirement_id:
                raise ValueError('This LSL stream is already mapped to another requirement.')
        self.mappings[requirement_id]=stream_uid

    def unmap(self, requirement_id: str) -> None:
        self.mappings.pop(requirement_id, None)

    def preflight(self, discovered: List[Dict[str, Any]]) -> Dict[str, Any]:
        by_uid={s.get('uid'):s for s in discovered if s.get('uid')}
        checks=[]
        for row in self.requirement_rows():
            uid=row.get('mapped_uid'); stream=by_uid.get(uid) if uid else None
            reasons=[]
            if row.get('required', True) and not uid: reasons.append('required stream is not mapped')
            if uid and not stream: reasons.append('mapped stream is not currently detected')
            if stream and row.get('modality') != 'OTHER' and stream.get('modality') not in (row.get('modality'),'OTHER'):
                reasons.append(f"modality mismatch: expected {row.get('modality')}, detected {stream.get('modality')}")
            if stream and stream.get('nominal_srate',0) < 0: reasons.append('invalid nominal sample rate')
            checks.append({**row,'detected_stream':stream,'ok':not reasons,'reasons':reasons})
        required=[c for c in checks if c.get('required',True)]
        return {'ready':all(c['ok'] for c in required), 'checks':checks,
                'summary':{'required':len(required),'passed':sum(c['ok'] for c in required),'total':len(checks)}}

class AcquisitionManager:
    def __init__(self): self._plans: Dict[str, AcquisitionPlan]={}
    def plan_for(self, experiment_id: str, requirements: List[Dict[str,Any]]) -> AcquisitionPlan:
        plan=self._plans.get(experiment_id)
        if plan is None or plan.requirements != requirements:
            plan=AcquisitionPlan(experiment_id, requirements); self._plans[experiment_id]=plan
        return plan
