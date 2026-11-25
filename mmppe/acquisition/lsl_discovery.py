from __future__ import annotations
from dataclasses import asdict, dataclass
import re
from typing import Any, Dict, List, Optional

try:
    from pylsl import StreamInlet, local_clock, resolve_streams
except Exception:
    StreamInlet = None
    local_clock = None
    resolve_streams = None

_MODALITY_PATTERNS = (
    ("EEG", ("eeg", "electroenceph")),
    ("ECG", ("ecg", "ekg", "electrocardio")),
    ("EMG", ("emg", "electromy")),
    ("EDA", ("eda", "gsr", "electrodermal", "skin conductance", "skinconductance")),
    ("EYE", ("eye", "gaze", "eyetracker", "eye tracker", "pupil")),
    ("AUDIO", ("audio", "microphone", "mic")),
    ("VIDEO", ("video", "camera", "webcam")),
)
# Participant IDs are not capped. Examples recognized: P1, P05, participant12, participant_103.
_PARTICIPANT_RE = re.compile(r"(?:^|[^a-z0-9])p(?:articipant)?[-_ ]?0*([0-9]+)(?:[^a-z0-9]|$)", re.I)


@dataclass
class StreamDescriptor:
    name: str
    type: str
    modality: str
    source_id: str
    uid: str
    hostname: str
    channel_count: int
    nominal_srate: float
    channel_format: str
    channel_labels: List[str]
    participant_hint: Optional[str]
    sample_available: bool
    sample_timestamp_lsl: Optional[float]
    warnings: List[str]

    def dict(self) -> Dict[str, Any]:
        return asdict(self)


def lsl_available() -> bool:
    return StreamInlet is not None and resolve_streams is not None and local_clock is not None


def _child_text(node: Any, name: str) -> str:
    try:
        return node.child(name).child_value() or ""
    except Exception:
        return ""


def _channel_labels(info: Any) -> List[str]:
    labels: List[str] = []
    try:
        ch = info.desc().child("channels").child("channel")
        for _ in range(int(info.channel_count())):
            labels.append(_child_text(ch, "label") or _child_text(ch, "name"))
            ch = ch.next_sibling()
    except Exception:
        pass
    return labels


def classify_modality(name: str, stream_type: str, labels: Optional[List[str]] = None) -> str:
    haystack = " ".join([name or "", stream_type or "", *(labels or [])]).lower()
    for modality, aliases in _MODALITY_PATTERNS:
        if any(alias in haystack for alias in aliases):
            return modality
    return "OTHER"


def participant_hint(name: str, stream_type: str, source_id: str) -> Optional[str]:
    match = _PARTICIPANT_RE.search(" ".join((name or "", stream_type or "", source_id or "")))
    return f"P{int(match.group(1)):02d}" if match else None


def scan_streams(timeout: float = 1.5, pull_sample: bool = False) -> Dict[str, Any]:
    if not lsl_available():
        return {"available": False, "streams": [], "error": "pylsl/liblsl unavailable"}
    try:
        infos = resolve_streams(wait_time=timeout)
    except Exception as exc:
        return {"available": True, "streams": [], "error": str(exc)}

    found: List[StreamDescriptor] = []
    for info in infos:
        warnings: List[str] = []
        labels = _channel_labels(info)
        name, stream_type, source_id = info.name() or "", info.type() or "", info.source_id() or ""
        channel_count, nominal_srate = int(info.channel_count()), float(info.nominal_srate())
        sample_available, sample_ts = False, None
        if pull_sample and nominal_srate > 0:
            try:
                inlet = StreamInlet(info, max_buflen=2, recover=True)
                sample, ts = inlet.pull_sample(timeout=0.35)
                sample_available = sample is not None
                sample_ts = float(ts) if sample is not None else None
            except Exception as exc:
                warnings.append(f"Sample pull failed: {exc}")
        found.append(StreamDescriptor(
            name=name, type=stream_type, modality=classify_modality(name, stream_type, labels),
            source_id=source_id, uid=info.uid() or "", hostname=info.hostname() or "",
            channel_count=channel_count, nominal_srate=nominal_srate,
            channel_format=str(info.channel_format()), channel_labels=labels,
            participant_hint=participant_hint(name, stream_type, source_id),
            sample_available=sample_available, sample_timestamp_lsl=sample_ts, warnings=warnings,
        ))
    return {"available": True, "lsl_clock": float(local_clock()), "streams": [s.dict() for s in found], "error": None}
