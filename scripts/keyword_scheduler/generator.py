"""Multi-dimensional keyword candidate generator.

Reads dimensions and templates from config, produces deduplicated candidates
with metadata (template_id, generation_source, risk_level, priority_hint).
Output: suggested_keywords.csv for human review.
"""

import csv
import itertools
import json
from pathlib import Path


def load_dimensions_config(config_path: Path) -> dict:
    """Load keyword dimensions config."""
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_existing_patterns(keywords_path: Path, expansions: dict | None = None) -> set[str]:
    """Load existing keyword patterns from search_keywords.csv for dedup.

    Expands [city]/[country] placeholders so concrete generated patterns
    can match against template-based existing keywords.
    """
    patterns = set()
    if not keywords_path.exists():
        return patterns
    with open(keywords_path, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            p = row.get("keyword_pattern", "").strip().lower()
            if not p:
                continue
            patterns.add(p)
            # Expand placeholders if expansions provided
            if expansions:
                import itertools as _it
                ph_lists = {}
                for ph, vals in expansions.items():
                    tag = f"[{ph}]"
                    if tag in p:
                        ph_lists[tag] = [v.lower() for v in vals]
                if ph_lists:
                    tags = list(ph_lists.keys())
                    for combo in _it.product(*ph_lists.values()):
                        expanded = p
                        for tag, val in zip(tags, combo):
                            expanded = expanded.replace(tag, val, 1)
                        patterns.add(expanded)
    return patterns


def generate_candidates(config_path: Path, existing_patterns: set[str] | None = None) -> list[dict]:
    """Generate keyword candidates from dimensions × templates.

    Quota is distributed evenly across templates so that early templates
    cannot consume the entire max_candidates budget. Each template gets
    at least min_per_template (default 2) candidates when possible.

    Returns list of dicts, each with:
      - keyword_pattern: the concrete search query string
      - template_id: which template produced it (e.g. "T1")
      - generation_source: "generator"
      - risk_level: "low" / "medium" / "high" based on template specificity
      - priority_hint: from template config ("high" / "medium" / "low")
      - dimensions_used: dict of which dimension values were used
    """
    config = load_dimensions_config(config_path)
    dimensions = config["dimensions"]
    templates = config["query_templates"]
    max_candidates = config.get("max_candidates", 200)
    min_per_template = config.get("min_per_template", 2)

    # Phase 1: compute how many combos each template can produce
    template_info = []
    for template in templates:
        tid = template["id"]
        pattern = template["pattern"]
        priority_hint = template.get("priority_hint", "medium")

        placeholders = _extract_placeholders(pattern)
        if not placeholders:
            continue

        dim_values = {}
        valid = True
        for ph in placeholders:
            vals = dimensions.get(ph, [])
            if not vals:
                valid = False
                break
            dim_values[ph] = vals

        if not valid:
            continue

        # Compute total possible combos
        total_combos = 1
        for vals in dim_values.values():
            total_combos *= len(vals)

        template_info.append({
            "id": tid,
            "pattern": pattern,
            "priority_hint": priority_hint,
            "dim_values": dim_values,
            "total_combos": total_combos,
        })

    if not template_info:
        return []

    # Phase 2: distribute quota across templates with priority weighting
    # High-priority templates (proven strategies like regional_town) get 2x quota
    _PRIORITY_MULTIPLIER = {"high": 2.0, "medium": 1.0, "low": 0.5}
    total_weight = sum(_PRIORITY_MULTIPLIER.get(t["priority_hint"], 1.0) for t in template_info)
    remaining = max_candidates

    candidates = []
    seen_patterns: set[str] = set()

    for info in template_info:
        tid = info["id"]
        pattern = info["pattern"]
        priority_hint = info["priority_hint"]
        dim_values = info["dim_values"]

        # Weighted quota: high-priority templates get proportionally more
        weight = _PRIORITY_MULTIPLIER.get(priority_hint, 1.0)
        base_quota = max(int(max_candidates * weight / total_weight), min_per_template)
        # This template's quota: min of base_quota, remaining budget, and total combos
        quota = min(base_quota, remaining, info["total_combos"])

        ph_names = list(dim_values.keys())
        ph_lists = [dim_values[ph] for ph in ph_names]

        # Round-robin across customer_type to avoid concentrating on one value
        combos = _distribute_combos(ph_names, ph_lists)

        count = 0
        for combo in combos:
            if count >= quota:
                break

            concrete = pattern
            used = {}
            for ph_name, val in zip(ph_names, combo):
                concrete = concrete.replace("{" + ph_name + "}", val, 1)
                used[ph_name] = val

            if concrete in seen_patterns:
                continue
            if existing_patterns and concrete.lower() in existing_patterns:
                continue
            seen_patterns.add(concrete)

            risk = _assess_risk(used, tid)

            candidates.append({
                "keyword_pattern": concrete,
                "template_id": tid,
                "generation_source": "generator",
                "risk_level": risk,
                "priority_hint": priority_hint,
                "dimensions_used": used,
            })
            count += 1
            remaining -= 1

        if remaining <= 0:
            break

    return candidates


def _distribute_combos(ph_names: list[str], ph_lists: list[list[str]]) -> list[tuple]:
    """Generate combos with round-robin across customer_type.

    Ensures all customer_type values are represented before any single
    value exhausts its share of other dimensions. Produces the full
    Cartesian product but ordered so customer_types are interleaved.
    """
    # Find customer_type index if present
    ct_idx = None
    for i, name in enumerate(ph_names):
        if name == "customer_type":
            ct_idx = i
            break

    if ct_idx is None:
        return list(itertools.product(*ph_lists))

    ct_values = ph_lists[ct_idx]
    other_lists = [ph_lists[i] for i in range(len(ph_lists)) if i != ct_idx]
    other_combos = list(itertools.product(*other_lists)) if other_lists else [()]

    # Full product: for each ct_val, pair with all other combos
    # but interleave so ct_vals are cycled through
    combos = []
    for other_combo in other_combos:
        for ct_val in ct_values:
            full = list(other_combo)
            full.insert(ct_idx, ct_val)
            combos.append(tuple(full))

    return combos


def _extract_placeholders(pattern: str) -> list[str]:
    """Extract {dimension_name} placeholders from a template pattern."""
    import re
    return re.findall(r"\{(\w+)\}", pattern)


def _assess_risk(dimensions_used: dict, template_id: str) -> str:
    """Assess risk level of a generated keyword.

    low = generic broad query (few dimensions, no quotes)
    medium = moderately specific
    high = very specific (uses role, source_modifier, trigger_event)
    """
    risky_dims = {"role", "source_modifier", "trigger_event"}
    used_risky = risky_dims & set(dimensions_used.keys())

    if len(used_risky) >= 2:
        return "high"
    elif len(used_risky) == 1:
        return "medium"
    else:
        return "low"


def write_suggested_csv(candidates: list[dict], output_path: Path) -> Path:
    """Write candidates to suggested_keywords.csv for human review.

    Columns: keyword_pattern, template_id, generation_source, risk_level,
             priority_hint, score, customer_type, role, geo, intent, org_form,
             source_modifier, trigger_event, review_status
    """
    fieldnames = [
        "keyword_pattern", "template_id", "generation_source", "risk_level",
        "priority_hint", "score", "customer_type", "role", "geo", "intent",
        "org_form", "source_modifier", "trigger_event", "review_status",
    ]

    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for c in candidates:
            dims = c.get("dimensions_used", {})
            writer.writerow({
                "keyword_pattern": c["keyword_pattern"],
                "template_id": c["template_id"],
                "generation_source": c["generation_source"],
                "risk_level": c["risk_level"],
                "priority_hint": c["priority_hint"],
                "score": c.get("score", ""),
                "customer_type": dims.get("customer_type", ""),
                "role": dims.get("role", ""),
                "geo": dims.get("geo", ""),
                "intent": dims.get("intent", ""),
                "org_form": dims.get("org_form", ""),
                "source_modifier": dims.get("source_modifier", ""),
                "trigger_event": dims.get("trigger_event", ""),
                "review_status": "pending",
            })

    return output_path


# --- CLI entry point ---

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate keyword candidates from dimensions × templates")
    parser.add_argument("--config", default=str(Path(__file__).resolve().parents[2] / "config" / "keyword_dimensions.json"))
    parser.add_argument("--output", default=str(Path(__file__).resolve().parents[2] / "reports" / "suggested_keywords.csv"))
    parser.add_argument("--max", type=int, default=None, help="Override max_candidates")
    parser.add_argument("--dry-run", action="store_true", help="Print candidates without writing CSV")
    args = parser.parse_args()

    config_path = Path(args.config)
    output_path = Path(args.output)
    keywords_path = config_path.parent.parent / "data" / "search_keywords.csv"
    # Load expansions from scheduler config for placeholder dedup
    scheduler_config_path = config_path.parent / "keyword_scheduler.json"
    expansions = {}
    if scheduler_config_path.exists():
        with open(scheduler_config_path, "r", encoding="utf-8") as f:
            sc = json.load(f)
        expansions = sc.get("template_expansions", {})
    existing = load_existing_patterns(keywords_path, expansions)
    tmp_path = None

    # Override max_candidates if specified
    if args.max:
        config = load_dimensions_config(config_path)
        config["max_candidates"] = args.max
        tmp_path = config_path.parent / "_tmp_dimensions.json"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(config, f)
        config_path = tmp_path

    candidates = generate_candidates(config_path, existing)

    # Clean up temp file
    if tmp_path and tmp_path.exists():
        tmp_path.unlink()

    print(f"[Generator] Generated {len(candidates)} keyword candidates")

    # Summary by template
    from collections import Counter
    by_template = Counter(c["template_id"] for c in candidates)
    for tid, count in sorted(by_template.items()):
        print(f"  {tid}: {count} candidates")

    if args.dry_run:
        print("\n[Generator] Dry run — top 10:")
        for c in candidates[:10]:
            print(f"  [{c['template_id']}] [{c['risk_level']}] {c['keyword_pattern']}")
        return

    write_suggested_csv(candidates, output_path)
    print(f"[Generator] Wrote to {output_path}")


if __name__ == "__main__":
    main()
