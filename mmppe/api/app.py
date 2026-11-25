from __future__ import annotations
from pathlib import Path
from typing import Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response, StreamingResponse
import csv, io, json, zipfile
from pydantic import BaseModel
from mmppe.core.schemas import ExperimentConfig
from mmppe.acquisition.lsl_discovery import scan_streams
from mmppe.experiments.registry import ExperimentRegistry
from mmppe.runtime.engine import RuntimeManager
from mmppe.acquisition.mapping import AcquisitionManager

ROOT = Path(__file__).resolve().parents[2]
registry = ExperimentRegistry(ROOT / "experiments")
runtimes = RuntimeManager()
acquisition = AcquisitionManager()
app = FastAPI(title="MMPPE", version="0.4.1-rc1")
UI_INDEX = ROOT / "mmppe" / "ui" / "index.html"

class ResponseSubmission(BaseModel):
    participant_id: str
    value: Any

class ParticipantAction(BaseModel):
    participant_id: str

@app.get("/", include_in_schema=False)
def root():
    return FileResponse(ROOT / "mmppe" / "ui" / "studio.html")

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)

@app.get("/api/health")
def health():
    return {"ok": True, "version": "0.4.1-rc1"}

@app.get("/api/experiments")
def experiments():
    return {k: v.model_dump() for k, v in registry.discover().items()}


@app.post("/api/experiments")
def save_experiment(config: ExperimentConfig):
    import json, re
    if not re.fullmatch(r"[A-Za-z0-9_-]+", config.id):
        raise HTTPException(422, "Experiment ID may contain only letters, numbers, underscore, and hyphen.")
    folder = ROOT / "experiments" / config.id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "experiment.json").write_text(json.dumps(config.model_dump(), indent=2), encoding="utf-8")
    return {"ok": True, "experiment_id": config.id, "path": str(folder.relative_to(ROOT))}

@app.get("/api/experiments/{experiment_id}")
def experiment(experiment_id: str):
    found = registry.discover()
    if experiment_id not in found:
        raise HTTPException(404, "Experiment not found")
    return found[experiment_id].model_dump()

@app.post("/api/runtime/{experiment_id}")
def create_runtime(experiment_id: str):
    found = registry.discover()
    if experiment_id not in found:
        raise HTTPException(404, "Experiment not found")
    return runtimes.create(found[experiment_id]).snapshot()

@app.get("/api/runtime/{runtime_id}")
def runtime_state(runtime_id: str):
    try: return runtimes.get(runtime_id).snapshot()
    except KeyError: raise HTTPException(404, "Runtime not found")


@app.post("/api/runtime/{runtime_id}/connect")
def runtime_connect(runtime_id: str, action: ParticipantAction):
    try: return runtimes.get(runtime_id).connect(action.participant_id)
    except KeyError: raise HTTPException(404, "Runtime not found")
    except ValueError as e: raise HTTPException(409, str(e))

@app.post("/api/runtime/{runtime_id}/disconnect")
def runtime_disconnect(runtime_id: str, action: ParticipantAction):
    try: return runtimes.get(runtime_id).disconnect(action.participant_id)
    except KeyError: raise HTTPException(404, "Runtime not found")
    except ValueError as e: raise HTTPException(409, str(e))

@app.post("/api/runtime/{runtime_id}/start")
def runtime_start(runtime_id: str):
    try: return runtimes.get(runtime_id).start()
    except KeyError: raise HTTPException(404, "Runtime not found")
    except ValueError as e: raise HTTPException(409, str(e))

@app.post("/api/runtime/{runtime_id}/advance")
def runtime_advance(runtime_id: str):
    try: return runtimes.get(runtime_id).advance()
    except KeyError: raise HTTPException(404, "Runtime not found")
    except ValueError as e: raise HTTPException(409, str(e))

@app.post("/api/runtime/{runtime_id}/response")
def runtime_response(runtime_id: str, submission: ResponseSubmission):
    try: return runtimes.get(runtime_id).submit_response(submission.participant_id, submission.value)
    except KeyError: raise HTTPException(404, "Runtime not found")
    except ValueError as e: raise HTTPException(409, str(e))

@app.get("/api/runtime/{runtime_id}/events")
def runtime_events(runtime_id: str):
    try: return runtimes.get(runtime_id).events
    except KeyError: raise HTTPException(404, "Runtime not found")

@app.get("/api/runtime/{runtime_id}/responses")
def runtime_responses(runtime_id: str):
    try: return runtimes.get(runtime_id).responses
    except KeyError: raise HTTPException(404, "Runtime not found")

@app.get("/api/acquisition/streams")
def acquisition_streams(pull_sample: bool = False):
    return scan_streams(pull_sample=pull_sample)


class StreamMappingSubmission(BaseModel):
    requirement_id: str
    stream_uid: str

def _plan(experiment_id: str):
    found=registry.discover()
    if experiment_id not in found: raise HTTPException(404, "Experiment not found")
    cfg=found[experiment_id]
    return acquisition.plan_for(experiment_id,[x.model_dump() for x in cfg.streams])

@app.get("/api/acquisition/{experiment_id}/plan")
def acquisition_plan(experiment_id: str):
    return {"experiment_id":experiment_id,"requirements":_plan(experiment_id).requirement_rows()}

@app.post("/api/acquisition/{experiment_id}/map")
def acquisition_map(experiment_id: str, submission: StreamMappingSubmission):
    try:
        plan=_plan(experiment_id); plan.map(submission.requirement_id, submission.stream_uid)
        return {"ok":True,"requirements":plan.requirement_rows()}
    except ValueError as e: raise HTTPException(409,str(e))

@app.delete("/api/acquisition/{experiment_id}/map/{requirement_id}")
def acquisition_unmap(experiment_id: str, requirement_id: str):
    _plan(experiment_id).unmap(requirement_id)
    return {"ok":True,"requirements":_plan(experiment_id).requirement_rows()}

@app.get("/api/acquisition/{experiment_id}/preflight")
def acquisition_preflight(experiment_id: str):
    scan=scan_streams(pull_sample=False)
    result=_plan(experiment_id).preflight(scan.get("streams",[]))
    return {**result,"lsl_available":scan.get("available",False),"scan_error":scan.get("error")}


@app.get("/showcase", include_in_schema=False)
def showcase():
    return FileResponse(ROOT / "mmppe" / "ui" / "showcase.html")

@app.get("/p{participant_number}", include_in_schema=False)
def participant_window(participant_number: int):
    if not 1 <= participant_number <= 20:
        raise HTTPException(404, "Participant window not found")
    return FileResponse(ROOT / "mmppe" / "ui" / "participant.html")

@app.get("/participant", include_in_schema=False)
def participant_window_default():
    return FileResponse(ROOT / "mmppe" / "ui" / "participant.html")

@app.get("/observer", include_in_schema=False)
def observer():
    return FileResponse(ROOT / "mmppe" / "ui" / "observer.html")

@app.post("/api/runtime/{runtime_id}/pause")
def runtime_pause(runtime_id: str):
    try: return runtimes.get(runtime_id).pause()
    except KeyError: raise HTTPException(404, "Runtime not found")
    except ValueError as e: raise HTTPException(409, str(e))

@app.post("/api/runtime/{runtime_id}/resume")
def runtime_resume(runtime_id: str):
    try: return runtimes.get(runtime_id).resume()
    except KeyError: raise HTTPException(404, "Runtime not found")
    except ValueError as e: raise HTTPException(409, str(e))

@app.get("/api/showcase/current")
def showcase_current():
    return {"runtime_id": getattr(app.state,"showcase_runtime_id",None)}

@app.post("/api/showcase/select/{experiment_id}")
def showcase_select(experiment_id: str):
    found=registry.discover()
    if experiment_id not in found: raise HTTPException(404,"Experiment not found")
    r=runtimes.create(found[experiment_id]);app.state.showcase_runtime_id=r.runtime_id
    return r.snapshot()

@app.get("/demo.css", include_in_schema=False)
def demo_css():
    return FileResponse(ROOT / "mmppe" / "ui" / "demo.css", media_type="text/css")

@app.get("/assets/participant.js", include_in_schema=False)
def participant_script():
    return FileResponse(ROOT / "mmppe" / "ui" / "participant.js", media_type="application/javascript")

@app.get("/demo.js", include_in_schema=False)
def demo_js():
    return FileResponse(ROOT / "mmppe" / "ui" / "demo.js", media_type="application/javascript")


@app.get("/api/runtime/{runtime_id}/export")
def export_session(runtime_id: str):
    """Export behavioral demo data, not LSL/XDF physiological recordings."""
    try: r=runtimes.get(runtime_id)
    except KeyError: raise HTTPException(404,"Runtime not found")
    def make_csv(rows, fields):
        output=io.StringIO(newline="")
        writer=csv.DictWriter(output,fieldnames=fields,extrasaction="ignore")
        writer.writeheader()
        for row in rows: writer.writerow({k:json.dumps(row[k],ensure_ascii=False) if isinstance(row.get(k),(dict,list)) else row.get(k,"") for k in fields})
        return output.getvalue()
    ev_fields=["timestamp_utc","event","runtime_id","experiment_id","repetition","phase_id","participant_id","active_participants"]
    resp_fields=["timestamp_utc","participant_id","phase_id","repetition","value"]
    package={"format":"mmppe-session-v1","demo_mode":True,"participant_inputs":"demonstration_browser_entries","sensor_data_collected":False,"experiment":r.config.model_dump(),"snapshot":r.snapshot(),"events":r.events,"responses":r.responses}
    out=io.BytesIO()
    with zipfile.ZipFile(out,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("session.json",json.dumps(package,indent=2,ensure_ascii=False,default=str))
        z.writestr("events.csv",make_csv(r.events,ev_fields))
        z.writestr("responses.csv",make_csv(r.responses,resp_fields))
        z.writestr("experiment_config.json",json.dumps(r.config.model_dump(),indent=2))
        z.writestr("README.txt","MMPPE symposium software demo export\nParticipant responses are demonstration browser entries; no human-subject research data.\nNo sensor, LSL, XDF, audio, or video recordings are included.\nTimes are UTC ISO-8601.\n")
    out.seek(0)
    return StreamingResponse(out,media_type="application/zip",headers={"Content-Disposition":f'attachment; filename="MMPPE_{runtime_id[:8]}_session_export.zip"'})

@app.get("/api/saved-sessions")
def saved_sessions():
    folder=ROOT/"data"/"sessions"
    result=[]
    for path in sorted(folder.glob("*.json"),key=lambda x:x.stat().st_mtime,reverse=True):
        try:
            data=json.loads(path.read_text(encoding="utf-8"))
            result.append({"runtime_id":path.stem,"experiment_name":data.get("snapshot",{}).get("experiment_name"),"status":data.get("snapshot",{}).get("status"),"events":len(data.get("events",[])),"responses":len(data.get("responses",[]))})
        except (OSError,ValueError): continue
    return result

@app.get("/studio", include_in_schema=False)
def studio():
    return FileResponse(ROOT / "mmppe" / "ui" / "studio.html")

@app.get("/studio.css", include_in_schema=False)
def studio_css():
    return FileResponse(ROOT / "mmppe" / "ui" / "studio.css", media_type="text/css")

@app.get("/studio.js", include_in_schema=False)
def studio_js():
    return FileResponse(ROOT / "mmppe" / "ui" / "studio.js", media_type="application/javascript")
