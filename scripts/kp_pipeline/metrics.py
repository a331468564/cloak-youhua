# scripts/kp_pipeline/metrics.py
import json
import csv
from datetime import datetime
from pathlib import Path
from collections import Counter

DATA_DIR = Path(__file__).parent.parent.parent / "data"


def init_metrics_log():
    log_path = DATA_DIR / "kp_metrics.json"
    if not log_path.exists():
        log_path.write_text("[]", encoding="utf-8")


def init_validation_log():
    log_path = DATA_DIR / "kp_validation_log.csv"
    if not log_path.exists():
        fields = [
            "timestamp", "run_id", "lead_id", "company_name",
            "candidate_name", "candidate_title", "candidate_type",
            "auto_score", "human_decision", "human_notes",
            "source_url", "confidence"
        ]
        with open(log_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fields, quoting=csv.QUOTE_ALL)
            writer.writeheader()


def log_run_metrics(run_id, stage, metrics_dict):
    log_path = DATA_DIR / "kp_metrics.json"
    entries = []
    if log_path.exists():
        try:
            entries = json.loads(log_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError):
            entries = []

    entry = {
        "run_id": run_id,
        "stage": stage,
        "timestamp": datetime.now().isoformat(),
        **metrics_dict,
    }
    entries.append(entry)
    log_path.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
    return entry


def log_validation_decision(run_id, lead_id, company_name, candidate_name,
                            candidate_title, candidate_type, auto_score,
                            human_decision, human_notes, source_url, confidence):
    log_path = DATA_DIR / "kp_validation_log.csv"
    fields = [
        "timestamp", "run_id", "lead_id", "company_name",
        "candidate_name", "candidate_title", "candidate_type",
        "auto_score", "human_decision", "human_notes",
        "source_url", "confidence"
    ]
    row = {
        "timestamp": datetime.now().isoformat(),
        "run_id": run_id,
        "lead_id": lead_id,
        "company_name": company_name,
        "candidate_name": candidate_name,
        "candidate_title": candidate_title,
        "candidate_type": candidate_type,
        "auto_score": str(auto_score),
        "human_decision": human_decision,
        "human_notes": human_notes,
        "source_url": source_url,
        "confidence": confidence,
    }
    with open(log_path, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, quoting=csv.QUOTE_ALL)
        writer.writerow(row)


def compute_accuracy_metrics(validation_log_path=None):
    log_path = validation_log_path or (DATA_DIR / "kp_validation_log.csv")
    if not log_path.exists():
        return {}

    rows = []
    with open(log_path, "r", newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            rows.append(row)

    if not rows:
        return {"total_decisions": 0}

    decisions = Counter(r.get("human_decision", "") for r in rows)
    total = len(rows)
    correct = decisions.get("correct", 0) + decisions.get("approved", 0)
    incorrect = decisions.get("incorrect", 0) + decisions.get("rejected", 0)
    uncertain = decisions.get("uncertain", 0) + decisions.get("skip", 0)

    return {
        "total_decisions": total,
        "approved": correct,
        "rejected": incorrect,
        "uncertain": uncertain,
        "accuracy_rate": round(correct / max(total - uncertain, 1), 3),
        "false_positive_rate": round(incorrect / max(total, 1), 3),
    }
