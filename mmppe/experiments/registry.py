from __future__ import annotations
from pathlib import Path
from typing import Dict
from mmppe.core.config import load_experiment_config
from mmppe.core.schemas import ExperimentConfig


class ExperimentRegistry:
    def __init__(self, root: str | Path):
        self.root = Path(root)

    def discover(self) -> Dict[str, ExperimentConfig]:
        experiments: Dict[str, ExperimentConfig] = {}
        if not self.root.exists():
            return experiments
        for config_path in sorted(self.root.glob("*/experiment.json")):
            config = load_experiment_config(config_path)
            experiments[config.id] = config
        return experiments
