from pathlib import Path
from mmppe.core.config import load_experiment_config
from mmppe.acquisition.lsl_discovery import classify_modality, participant_hint

ROOT = Path(__file__).resolve().parents[1]

def test_single_participant_config_loads():
    cfg = load_experiment_config(ROOT / "experiments" / "demo_single_participant" / "experiment.json")
    assert len(cfg.participants) == 1
    assert cfg.participants[0].id == "P01"

def test_vendor_neutral_modality_classification():
    assert classify_modality("ResearchAmp", "EEG", []) == "EEG"
    assert classify_modality("Sensor", "EDA", []) == "EDA"

def test_participant_hint_not_limited_to_five():
    assert participant_hint("EEG Participant 12", "EEG", "") == "P12"


def test_launcher_self_check_imports():
    from mmppe.api.app import app
    from mmppe.acquisition.lsl_discovery import classify_modality
    assert app is not None
    assert classify_modality("ResearchAmp", "EEG", []) == "EEG"
