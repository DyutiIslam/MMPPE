from __future__ import annotations
import argparse, json, socket, subprocess, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def import_check() -> None:
    from mmppe.api.app import app
    from mmppe.acquisition.lsl_discovery import classify_modality, participant_hint
    from mmppe.core.config import load_experiment_config
    assert app is not None
    assert classify_modality("GenericResearchAmp", "EEG", []) == "EEG"
    assert classify_modality("GenericSensor", "GSR", []) == "EDA"
    assert participant_hint("Participant 12 EEG", "EEG", "") == "P12"
    cfg = load_experiment_config(ROOT / "experiments" / "demo_single_participant" / "experiment.json")
    multi = load_experiment_config(ROOT / "experiments" / "demo_collaborative_rating" / "experiment.json")
    assert len(cfg.participants) == 1
    assert len(multi.participants) == 3
    assert not any(v in str(multi.model_dump()).lower() for v in ("emotiv", "shimmer"))
    print("Package/import/config checks: PASS")

def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])

def boot_check() -> None:
    port = free_port()
    proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "mmppe.api.app:app", "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    url = f"http://127.0.0.1:{port}/api/health"
    try:
        deadline = time.time() + 12
        last = None
        while time.time() < deadline:
            if proc.poll() is not None:
                out = proc.stdout.read() if proc.stdout else ""
                raise RuntimeError(f"Server exited early ({proc.returncode}). {out}")
            try:
                with urllib.request.urlopen(url, timeout=1) as r:
                    payload = json.loads(r.read().decode())
                if payload.get("ok") is True:
                    print(f"Application boot/health check: PASS ({url})")
                    return
                last = payload
            except Exception as exc:
                last = exc
            time.sleep(.25)
        raise RuntimeError(f"Health endpoint did not become ready: {last}")
    finally:
        proc.terminate()
        try: proc.wait(timeout=4)
        except subprocess.TimeoutExpired:
            proc.kill(); proc.wait(timeout=2)

def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("--imports",action="store_true"); p.add_argument("--boot",action="store_true"); a=p.parse_args()
    try:
        if a.imports: import_check()
        if a.boot: boot_check()
        if not (a.imports or a.boot): import_check(); boot_check()
        return 0
    except Exception as exc:
        print(f"RELEASE CHECK FAILED: {exc}", file=sys.stderr); return 1
if __name__ == "__main__": raise SystemExit(main())
