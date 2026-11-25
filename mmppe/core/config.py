from __future__ import annotations
import json
from pathlib import Path
from .schemas import ExperimentConfig


def load_experiment_config(path: str | Path) -> ExperimentConfig:
    path = Path(path)
    if path.suffix.lower() != ".json":
        raise ValueError("MMPPE supports JSON experiment definitions. YAML can be added later.")
    with path.open("r", encoding="utf-8") as f:
        return ExperimentConfig.model_validate(json.load(f))
