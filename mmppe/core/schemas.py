from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, model_validator

# MMPPE is stream/device independent. These are semantic modality labels, not vendors.
Modality = Literal["EEG","ECG","EMG","EDA","PPG","EYE","IMU","AUDIO","VIDEO","BEHAVIOR","OTHER"]

class ParticipantConfig(BaseModel):
    id: str = Field(min_length=1)
    label: str = ""
    role: str = "participant"
    metadata: Dict[str, Any] = Field(default_factory=dict)

class StreamRequirement(BaseModel):
    modality: Modality
    participant_id: Optional[str] = None
    required: bool = True
    min_streams: int = Field(default=1, ge=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class PhaseConfig(BaseModel):
    id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    title: str = ""
    duration_sec: Optional[float] = Field(default=None, ge=0)
    stimulus: Optional[Dict[str, Any]] = None
    response: Optional[Dict[str, Any]] = None
    participants: Optional[List[str]] = None  # None = all participants
    advance_when: Literal["timer","moderator","all_responses"] = "moderator"
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ExperimentConfig(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = ""
    version: str = "0.3"
    participants: List[ParticipantConfig] = Field(min_length=1)
    phases: List[PhaseConfig] = Field(min_length=1)
    streams: List[StreamRequirement] = Field(default_factory=list)
    repetitions: int = Field(default=1, ge=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_references(self):
        ids=[p.id for p in self.participants]
        if len(ids)!=len(set(ids)): raise ValueError("Participant IDs must be unique.")
        known=set(ids)
        unknown=sorted({s.participant_id for s in self.streams if s.participant_id and s.participant_id not in known})
        if unknown: raise ValueError(f"Stream requirements reference unknown participants: {unknown}")
        for phase in self.phases:
            bad=sorted(set(phase.participants or [])-known)
            if bad: raise ValueError(f"Phase '{phase.id}' references unknown participants: {bad}")
        phase_ids=[p.id for p in self.phases]
        if len(phase_ids)!=len(set(phase_ids)): raise ValueError("Phase IDs must be unique.")
        return self
