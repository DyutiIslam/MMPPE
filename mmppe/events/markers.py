from __future__ import annotations
import json
from typing import Any, Dict, Optional

try:
    from pylsl import StreamInfo, StreamOutlet, local_clock
except Exception:
    StreamInfo = StreamOutlet = local_clock = None

STREAM_NAME = "MMPPE_Markers"
STREAM_TYPE = "Markers"
SOURCE_ID = "mmppe_runtime"
_outlet = None


def available() -> bool:
    return all(x is not None for x in (StreamInfo, StreamOutlet, local_clock))


def get_outlet():
    global _outlet
    if not available():
        return None
    if _outlet is None:
        info = StreamInfo(STREAM_NAME, STREAM_TYPE, 1, 0, "string", SOURCE_ID)
        desc = info.desc()
        desc.append_child_value("manufacturer", "MMPPE")
        desc.append_child_value("content_type", "JSON experimental event markers")
        _outlet = StreamOutlet(info)
    return _outlet


def push(marker: str, payload: Optional[Dict[str, Any]] = None) -> Optional[float]:
    outlet = get_outlet()
    if outlet is None:
        return None
    ts = float(local_clock())
    outlet.push_sample([json.dumps({"marker": marker, "lsl_time": ts, **(payload or {})})], timestamp=ts)
    return ts
