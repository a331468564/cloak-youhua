import json
from pathlib import Path

_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "keyword_scheduler.json"

def load_config() -> dict:
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_template_expansions(config: dict) -> dict[str, list[str]]:
    return config.get("template_expansions", {})

def get_extraction_defaults(config: dict) -> dict:
    return config.get("extraction_defaults", {})
