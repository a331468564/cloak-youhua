# scripts/kp_pipeline/config.py
import json
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "kp_pipeline.json"


def load_config(config_path=None):
    path = config_path or CONFIG_PATH
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_stage_config(config, stage_name):
    return config.get("stages", {}).get(stage_name, {})
