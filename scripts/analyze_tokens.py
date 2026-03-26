#!/usr/bin/env python3
"""
Analyze token consumption from claude_process/{model}/{batch}/claude_thinking/*.jsonl files.
Outputs input token fields, output tokens, total tokens, and total duration
for each skill (use-skill / no-use-skill).

Usage:
    python scripts/analyze_tokens.py
    python scripts/analyze_tokens.py --config path/to/config.yaml

Column order (13 columns):
  1  skill name
  2  input_tokens (use)
  3  input_tokens (no-use)
  4  cache_creation_input (use)
  5  cache_creation_input (no-use)
  6  cache_read_input (use)
  7  cache_read_input (no-use)
  8  output_tokens (use)
  9  output_tokens (no-use)
  10 total_tokens (use)
  11 total_tokens (no-use)
  12 duration (use)
  13 duration (no-use)
"""

import json
import os
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

from dotenv import load_dotenv

load_dotenv()


def _get_model_name() -> str:
    """Get sanitized model name from ANTHROPIC_DEFAULT_SONNET_MODEL env var."""
    raw = os.environ.get("ANTHROPIC_DEFAULT_SONNET_MODEL", "unknown-model")
    return re.sub(r"[^A-Za-z0-9._-]+", "-", raw) or "unknown-model"


# ─── File parsing ────────────────────────────────────────────────────────────────


def parse_filename(name: str):
    """Parse filename, return skill_id and use_skill bool; return None on failure."""
    stem = name.removesuffix(".jsonl")
    pat = r"^claude_(.+)_use-agent-(true|false)_use-skill-(true|false)_\d{8}_\d{6}$"
    m = re.match(pat, stem)
    if not m:
        return None
    return {"skill_id": m.group(1), "use_skill": m.group(3) == "true"}


def parse_jsonl(path: Path) -> dict:
    """Read JSONL, accumulate all token fields and compute duration from first/last timestamps."""
    input_tokens = 0
    cache_creation = 0
    cache_read = 0
    output_tokens = 0
    timestamps = []

    with open(path, encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                continue

            ts = obj.get("timestamp")
            if ts:
                try:
                    timestamps.append(datetime.fromisoformat(ts.replace("Z", "+00:00")))
                except ValueError:
                    pass

            usage = obj.get("message", {}).get("usage", {})
            if isinstance(usage, dict):
                input_tokens += usage.get("input_tokens", 0)
                cache_creation += usage.get("cache_creation_input_tokens", 0)
                cache_read += usage.get("cache_read_input_tokens", 0)
                output_tokens += usage.get("output_tokens", 0)

    duration = 0.0
    if len(timestamps) >= 2:
        duration = (max(timestamps) - min(timestamps)).total_seconds()

    total = input_tokens + cache_creation + cache_read + output_tokens

    return {
        "input": input_tokens,
        "cache_create": cache_creation,
        "cache_read": cache_read,
        "output": output_tokens,
        "total": total,
        "duration": duration,
    }


# ─── Formatting ──────────────────────────────────────────────────────────────────


def fmt_n(n) -> str:
    """Format a number right-aligned 13 chars with thousands separator; show dash for zero."""
    return f"{n:>13,}" if n else f"{'—':>13}"


def fmt_d(s) -> str:
    """Format seconds as XmYs, right-aligned 9 chars."""
    if not s:
        return f"{'—':>9}"
    m, sec = divmod(int(s), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h{m:02d}m{sec:02d}s"
    return f"{m}m{sec:02d}s" if m else f"{sec}s"


# ─── Main logic ─────────────────────────────────────────────────────────────────────────────────────


def main():
    import argparse
    import yaml

    parser = argparse.ArgumentParser(
        description="Analyze token consumption from JSONL files"
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

    thinking_dir = (
        Path(__file__).resolve().parents[1]
        / "claude_process"
        / model_name
        / batch
        / "claude_thinking"
    )
    if not thinking_dir.exists():
        print(f"❌ Directory not found: {thinking_dir}")
        return

    # Group by skill_id -> {True: stats, False: stats}
    data: dict[str, dict] = defaultdict(dict)
    skipped = []

    for fp in sorted(thinking_dir.glob("*.jsonl")):
        info = parse_filename(fp.name)
        if not info:
            skipped.append(fp.name)
            continue
        data[info["skill_id"]][info["use_skill"]] = parse_jsonl(fp)

    if skipped:
        print(f"⚠  Skipped files that could not be parsed: {skipped}\n")

    # ─── Width constants ──────────────────────────────────────────────────────────
    W_SKILL = 38  # skill column width
    W_N = 13  # number column width
    W_D = 9  # duration column width
    SEP = " │ "

    def hh(label, w):
        return f"{label:^{(W_N*2)+1}}"

    total_width = W_SKILL + 2 + (W_N * 2 + 1) * 5 + 8 + (W_D * 2 + 1) + 2 + 4 * 3
    hr = "─" * (total_width + 2)

    u_label = f"{'use':^{W_N}}"
    n_label = f"{'no-use':^{W_N}}"
    un = f"{u_label} {n_label}"

    header1 = (
        f"{'skill':{W_SKILL}}{SEP}"
        f"{hh('input_tokens', W_N)}{SEP}"
        f"{hh('cache_create_input', W_N)}{SEP}"
        f"{hh('cache_read_input', W_N)}{SEP}"
        f"{hh('output_tokens', W_N)}{SEP}"
        f"{hh('total_tokens', W_N)}{SEP}"
        f"{hh('duration', W_D*2+1)}"
    )
    header2 = (
        f"{'(use / no-use)':{W_SKILL}}{SEP}"
        f"{un}{SEP}{un}{SEP}{un}{SEP}{un}{SEP}{un}{SEP}"
        f"{f'use':^{W_D}} {f'no-use':^{W_D}}"
    )

    # Build text output, CSV rows, and JSON structure simultaneously
    text_lines = []
    text_lines.append(hr)
    text_lines.append(header1)
    text_lines.append(header2)
    text_lines.append(hr)

    # ─── Summary accumulator ────────────────────────────────────────────────────────────────────
    keys = ("input", "cache_create", "cache_read", "output", "total")
    tot = {b: {k: 0 for k in keys} | {"duration": 0.0} for b in ("use", "nouse")}

    def v_n(st, key):
        return st[key] if st else 0

    def v_d(st):
        return st["duration"] if st else 0.0

    # CSV/JSON setup
    csv_rows = []
    json_obj = {}

    for skill in sorted(data.keys()):
        su = data[skill].get(True)
        sn = data[skill].get(False)

        cols = [f"{skill:<{W_SKILL}}"]
        # Text columns
        for key in keys:
            cols.append(f"{fmt_n(v_n(su, key))} {fmt_n(v_n(sn, key))}")
        cols.append(f"{fmt_d(v_d(su)):>{W_D}} {fmt_d(v_d(sn)):>{W_D}}")

        text_lines.append(SEP.join(cols))

        # Accumulate
        for key in keys:
            tot["use"][key] += v_n(su, key)
            tot["nouse"][key] += v_n(sn, key)
        tot["use"]["duration"] += v_d(su)
        tot["nouse"]["duration"] += v_d(sn)

        # CSV row (flattened)
        csv_rows.append(
            {
                "skill": skill,
                "input_use": v_n(su, "input"),
                "input_no_use": v_n(sn, "input"),
                "cache_create_use": v_n(su, "cache_create"),
                "cache_create_no_use": v_n(sn, "cache_create"),
                "cache_read_use": v_n(su, "cache_read"),
                "cache_read_no_use": v_n(sn, "cache_read"),
                "output_use": v_n(su, "output"),
                "output_no_use": v_n(sn, "output"),
                "total_use": v_n(su, "total"),
                "total_no_use": v_n(sn, "total"),
                "duration_use_seconds": int(v_d(su)),
                "duration_no_use_seconds": int(v_d(sn)),
            }
        )

        # JSON structure
        json_obj[skill] = {
            "use": {
                "input": v_n(su, "input"),
                "cache_create": v_n(su, "cache_create"),
                "cache_read": v_n(su, "cache_read"),
                "output": v_n(su, "output"),
                "total": v_n(su, "total"),
                "duration_seconds": int(v_d(su)),
            },
            "no_use": {
                "input": v_n(sn, "input"),
                "cache_create": v_n(sn, "cache_create"),
                "cache_read": v_n(sn, "cache_read"),
                "output": v_n(sn, "output"),
                "total": v_n(sn, "total"),
                "duration_seconds": int(v_d(sn)),
            },
        }

    # ─── Summary row ─────────────────────────────────────────────────────────────────────────
    text_lines.append(hr)
    total_cols = [f"{'TOTAL':<{W_SKILL}}"]
    for key in keys:
        total_cols.append(f"{fmt_n(tot['use'][key])} {fmt_n(tot['nouse'][key])}")
    total_cols.append(
        f"{fmt_d(tot['use']['duration']):>{W_D}} {fmt_d(tot['nouse']['duration']):>{W_D}}"
    )
    text_lines.append(SEP.join(total_cols))
    text_lines.append(hr)
    text_lines.append("")

    # Write to reports directory
    reports_dir = (
        Path(__file__).resolve().parents[1]
        / "reports"
        / model_name
        / batch
        / "token_and_duration"
    )
    reports_dir.mkdir(parents=True, exist_ok=True)

    # CSV
    import csv

    csv_path = reports_dir / "token_report.csv"
    csv_fieldnames = [
        "skill",
        "input_use",
        "input_no_use",
        "cache_create_use",
        "cache_create_no_use",
        "cache_read_use",
        "cache_read_no_use",
        "output_use",
        "output_no_use",
        "total_use",
        "total_no_use",
        "duration_use_seconds",
        "duration_no_use_seconds",
    ]
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fieldnames)
        writer.writeheader()
        for row in csv_rows:
            writer.writerow(row)

    # JSON
    json_path = reports_dir / "token_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "summary": {"use": tot["use"], "no_use": tot["nouse"]},
                "skills": json_obj,
            },
            f,
            indent=2,
        )


if __name__ == "__main__":
    main()
