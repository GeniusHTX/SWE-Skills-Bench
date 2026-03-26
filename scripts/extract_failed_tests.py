"""
Extract failed unit tests from eval_report_*.json files and generate
comparison tables (CSV + JSON) under reports/{model}/{batch}/failed_test/.


Usage:
    python scripts/extract_failed_tests.py
    python scripts/extract_failed_tests.py --config path/to/config.yaml

Rules:
- Only use the latest-timestamped file per (skill, use_skill) pair.
- Only extract entries where method == "unit_test".
- Column 4 = count of intersection (tests that failed in both use-skill=true
  and use-skill=false).
"""

import csv
import json
import os
import re
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Match: eval_report_{skill}_use-agent-true_use-skill-{true|false}_{date}_{time}.json
FILE_RE = re.compile(
    r"^eval_report_(?P<skill>.+?)_use-agent-true_use-skill-(?P<use_skill>true|false)_(?P<ts>\d{8}_\d{6})\.json$"
)


def collect_latest_files(eval_dir: Path) -> dict[tuple[str, str], Path]:
    """
    Return mapping of (skill, use_skill) -> Path of the latest JSON file.
    """
    latest: dict[tuple[str, str], tuple[str, Path]] = {}
    for fpath in eval_dir.glob("eval_report_*.json"):
        m = FILE_RE.match(fpath.name)
        if not m:
            continue
        key = (m.group("skill"), m.group("use_skill"))
        ts = m.group("ts")
        if key not in latest or ts > latest[key][0]:
            latest[key] = (ts, fpath)
    return {k: v[1] for k, v in latest.items()}


def extract_failed_tests(fpath: Path) -> list[str]:
    """
    Return list of failed test names (starting with 'test') from the unit_test
    evaluation entry in the given report file.
    """
    with open(fpath, encoding="utf-8") as f:
        data = json.load(f)

    details = data.get("evaluation_scores", {}).get("details") or []
    tests: list[str] = []
    for entry in details:
        if entry.get("method") != "unit_test":
            continue
        inner = entry.get("details") or {}
        failed = inner.get("failed_tests") or []
        for item in failed:
            if isinstance(item, str) and item.lstrip().startswith("test"):
                tests.append(item.strip())
    return tests


def build_records(file_map: dict[tuple[str, str], Path]) -> list[dict]:
    """
    For every skill present in file_map, build one record with:
      skill, use_skill_true_failed (list), use_skill_false_failed (list),
      common_count (int)
    """
    # Group by skill
    by_skill: dict[str, dict[str, list[str]]] = defaultdict(dict)
    for (skill, use_skill), fpath in sorted(file_map.items()):
        by_skill[skill][use_skill] = extract_failed_tests(fpath)

    records = []
    for skill in sorted(by_skill.keys()):
        true_failed = by_skill[skill].get("true", [])
        false_failed = by_skill[skill].get("false", [])
        common_count = len(set(true_failed) & set(false_failed))
        records.append(
            {
                "skill": skill,
                "U": len(true_failed),
                "N": len(false_failed),
                "use_skill_true_failed": true_failed,
                "use_skill_false_failed": false_failed,
                "common_count": common_count,
            }
        )
    return records


def write_csv(records: list[dict], output_path: Path) -> None:
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        # CSV header using U/N prefixes as requested
        writer.writerow(
            [
                "skill",
                "U-failed_tests",
                "N-failed_tests",
                "U-failed_cnt",
                "N-failed_cnt",
                "common_count",
            ]
        )
        for r in records:
            writer.writerow(
                [
                    r["skill"],
                    "; ".join(r["use_skill_true_failed"]),
                    "; ".join(r["use_skill_false_failed"]),
                    r.get("U", 0),
                    r.get("N", 0),
                    r["common_count"],
                ]
            )
        # Summary row: sum count columns only; leave failed test list column empty
        total_U = sum(r.get("U", 0) for r in records)
        total_N = sum(r.get("N", 0) for r in records)
        total_common = sum(r.get("common_count", 0) for r in records)
        writer.writerow(
            [
                "TOTAL",
                "",
                "",
                total_U,
                total_N,
                total_common,
            ]
        )


def write_json(records: list[dict], output_path: Path) -> None:
    # Transform records to use U-/N- prefixed keys for JSON output
    out = []
    for r in records:
        out.append(
            {
                "skill": r["skill"],
                "U-failed_tests": r.get("use_skill_true_failed", []),
                "N-failed_tests": r.get("use_skill_false_failed", []),
                "U-failed_cnt": r.get("U", 0),
                "N-failed_cnt": r.get("N", 0),
                "common_count": r.get("common_count", 0),
            }
        )
    summary = {
        "total_U_failed_cnt": sum(r.get("U", 0) for r in records),
        "total_N_failed_cnt": sum(r.get("N", 0) for r in records),
        "total_common_count": sum(r.get("common_count", 0) for r in records),
        "skills_count": len(records),
    }
    payload = {"summary": summary, "skills": out}
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def main() -> None:
    import argparse
    import yaml

    parser = argparse.ArgumentParser(
        description="Extract failed unit tests from eval reports"
    )
    parser.add_argument(
        "--config", default="config/benchmark_config.yaml", help="Benchmark config file"
    )
    args = parser.parse_args()

    # Derive model name and active batch from config
    try:
        with open(args.config, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    except Exception:
        cfg = {}
    raw = os.environ.get("ANTHROPIC_DEFAULT_SONNET_MODEL", "unknown-model")
    model_name = re.sub(r"[^A-Za-z0-9._-]+", "-", raw) or "unknown-model"
    g = cfg.get("global", {})
    batch = g.get("active_batch")
    if not batch:
        batches = g.get("batches", [])
        batch = str(batches[0]) if batches else "batch1"
    batch = str(batch)

    eval_dir = Path(__file__).parent.parent / "reports" / model_name / batch / "eval"
    output_dir = (
        Path(__file__).parent.parent / "reports" / model_name / batch / "failed_test"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    file_map = collect_latest_files(eval_dir)
    print(f"Found {len(file_map)} (skill, use_skill) pairs across {eval_dir}")

    records = build_records(file_map)
    print(f"Built {len(records)} skill records")

    csv_path = output_dir / "failed_tests.csv"
    json_path = output_dir / "failed_tests.json"

    write_csv(records, csv_path)
    write_json(records, json_path)

    print(f"CSV  -> {csv_path}")
    print(f"JSON -> {json_path}")


if __name__ == "__main__":
    main()
