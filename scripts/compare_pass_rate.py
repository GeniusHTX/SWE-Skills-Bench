"""
compare_pass_rate.py
Compare L2/unit_test pass rates between use-skill and no-use-skill, output delta.

Usage examples:
    # Single skill
    python scripts/compare_pass_rate.py -s add-malli-schemas

    # Multiple skills
    python scripts/compare_pass_rate.py -s add-malli-schemas -s tdd-workflow

    # All skills
    python scripts/compare_pass_rate.py --all

    # Specify use-agent state (default: true)
    python scripts/compare_pass_rate.py --all --use-agent false

    # Output JSON
    python scripts/compare_pass_rate.py --all --format json
"""

import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime

import click
from dotenv import load_dotenv

load_dotenv()

_model_name = (
    re.sub(
        r"[^A-Za-z0-9._-]+",
        "-",
        os.environ.get("ANTHROPIC_DEFAULT_SONNET_MODEL", "unknown-model"),
    )
    or "unknown-model"
)

REPORT_DIR_DEFAULT = f"reports/{_model_name}/eval"
PATTERN = re.compile(
    r"^eval_report_(?P<skill>.+)_use-agent-(?P<ua>true|false)_use-skill-(?P<us>true|false)_(?P<ts>\d{8}_\d{6})\.json$"
)


def _extract_pass_rate(report_path: Path) -> dict:
    """Extract L2/unit_test passed, total, and pass_rate from a report file."""
    with open(report_path, encoding="utf-8") as f:
        data = json.load(f)

    details = data.get("evaluation_scores", {}).get("details", [])
    for item in details:
        if item.get("level") == "L2" and item.get("method") == "unit_test":
            d = item.get("details", {})
            total = d.get("total", 0)
            passed = d.get("passed", 0)
            rate = passed / total if total > 0 else None
            return {"passed": passed, "total": total, "pass_rate": rate}

    # L2/unit_test entry not found
    return {"passed": None, "total": None, "pass_rate": None}


def _latest_report(
    report_dir: Path, skill: str, use_agent: str, use_skill: str
) -> Path | None:
    """Return the most recent report matching the criteria (sorted by timestamp in filename descending)."""
    candidates = []
    for p in report_dir.glob(
        f"eval_report_{skill}_use-agent-{use_agent}_use-skill-{use_skill}_*.json"
    ):
        m = PATTERN.match(p.name)
        if m:
            candidates.append((m.group("ts"), p))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def _all_skills(report_dir: Path, use_agent: str) -> list:
    """Auto-discover all skill IDs from the report directory."""
    skills = set()
    for p in report_dir.glob("eval_report_*.json"):
        m = PATTERN.match(p.name)
        if m and m.group("ua") == use_agent:
            skills.add(m.group("skill"))
    return sorted(skills)


def _compute(report_dir: Path, skill: str, use_agent: str) -> dict:
    with_skill_file = _latest_report(report_dir, skill, use_agent, "true")
    no_skill_file = _latest_report(report_dir, skill, use_agent, "false")

    with_skill = _extract_pass_rate(with_skill_file) if with_skill_file else {}
    no_skill = _extract_pass_rate(no_skill_file) if no_skill_file else {}

    ws_rate = with_skill.get("pass_rate")
    ns_rate = no_skill.get("pass_rate")
    delta = (
        (ws_rate - ns_rate) if (ws_rate is not None and ns_rate is not None) else None
    )

    return {
        "skill_id": skill,
        "use_skill_file": with_skill_file.name if with_skill_file else None,
        "no_skill_file": no_skill_file.name if no_skill_file else None,
        "use_skill_passed": with_skill.get("passed"),
        "use_skill_total": with_skill.get("total"),
        "use_skill_pass_rate": ws_rate,
        "no_skill_passed": no_skill.get("passed"),
        "no_skill_total": no_skill.get("total"),
        "no_skill_pass_rate": ns_rate,
        "delta": delta,
    }


def _fmt_rate(v) -> str:
    return f"{v:.1%}" if v is not None else "N/A"


def _fmt_delta(v) -> str:
    if v is None:
        return "N/A"
    sign = "+" if v > 0 else ""
    return f"{sign}{v:.1%}"


@click.command()
@click.option(
    "--skill",
    "-s",
    "skills",
    multiple=True,
    help="Skill ID (can be specified multiple times)",
)
@click.option(
    "--all",
    "all_skills",
    is_flag=True,
    default=False,
    help="Process all skills in directory",
)
@click.option(
    "--use-agent",
    "-a",
    "use_agent",
    default="true",
    type=click.Choice(["true", "false"]),
    show_default=True,
    help="Corresponds to the --use-agent flag when running main.py",
)
@click.option(
    "--report-dir",
    "-d",
    default=REPORT_DIR_DEFAULT,
    show_default=True,
    help="Report source directory",
)
@click.option(
    "--output",
    "-o",
    "out_dir",
    default=f"reports/{_model_name}/compare",
    show_default=True,
    help="Output directory for comparison results",
)
@click.option(
    "--format",
    "-f",
    "fmt",
    default="table",
    type=click.Choice(["table", "json"]),
    show_default=True,
    help="Output format",
)
def main(skills, all_skills, use_agent, report_dir, out_dir, fmt):
    """Compare use-skill / no-use-skill L2/unit_test pass rates and output delta."""
    dir_path = Path(report_dir)
    if not dir_path.exists():
        click.echo(f"[ERROR] Report directory not found: {dir_path}", err=True)
        sys.exit(1)

    if all_skills:
        target_skills = _all_skills(dir_path, use_agent)
        if not target_skills:
            click.echo(
                f"[WARN] No reports found for use-agent={use_agent} in directory.",
                err=True,
            )
            sys.exit(0)
    elif skills:
        target_skills = list(skills)
    else:
        click.echo("[ERROR] Please specify --skill/-s or --all", err=True)
        sys.exit(1)

    rows = [_compute(dir_path, s, use_agent) for s in target_skills]

    # Ensure output directory exists
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # ── JSON output ─────────────────────────────────────────────────────
    if fmt == "json":
        payload = json.dumps(rows, ensure_ascii=False, indent=2)
        click.echo(payload)

        # Write to file
        fname = f"compare_{'all' if all_skills else '_'.join(target_skills)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        fp = out_path / fname
        with open(fp, "w", encoding="utf-8") as f:
            f.write(payload)
        click.echo(f"Saved comparison to: {fp}")
        return

    # ── Table output (build as string for both printing and saving)
    id_w = max((len(r["skill_id"]) for r in rows), default=8)
    id_w = max(id_w, 8)

    col_skill = id_w
    col_rate = 10
    col_detail = 14
    col_delta = 9

    header = (
        f"{'Skill ID':<{col_skill}}  "
        f"{'use-skill':>{col_rate}}  {'(pass/total)':<{col_detail}}  "
        f"{'no-skill':>{col_rate}}  {'(pass/total)':<{col_detail}}  "
        f"{'delta':>{col_delta}}"
    )
    sep = "─" * len(header)

    out_lines = [sep, header, sep]

    for r in rows:
        ws_detail = (
            f"({r['use_skill_passed']}/{r['use_skill_total']})"
            if r["use_skill_passed"] is not None
            else "(N/A)"
        )
        ns_detail = (
            f"({r['no_skill_passed']}/{r['no_skill_total']})"
            if r["no_skill_passed"] is not None
            else "(N/A)"
        )
        out_lines.append(
            f"{r['skill_id']:<{col_skill}}  "
            f"{_fmt_rate(r['use_skill_pass_rate']):>{col_rate}}  {ws_detail:<{col_detail}}  "
            f"{_fmt_rate(r['no_skill_pass_rate']):>{col_rate}}  {ns_detail:<{col_detail}}  "
            f"{_fmt_delta(r['delta']):>{col_delta}}"
        )

    out_lines.append(sep)

    valid = [r for r in rows if r["delta"] is not None]
    if valid:
        avg_delta = sum(r["delta"] for r in valid) / len(valid)
        label = f"Average ({len(valid)}/{len(rows)} skills)"
        padding = (
            col_skill
            + 2
            + col_rate
            + 2
            + col_detail
            + 2
            + col_rate
            + 2
            + col_detail
            + 2
        )
        out_lines.append(f"{label:<{padding}}{_fmt_delta(avg_delta):>{col_delta}}")
        out_lines.append(sep)

    table_str = "\n".join(out_lines)
    click.echo(table_str)

    # Write to file
    fname = f"compare_{'all' if all_skills else '_'.join(target_skills)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    fp = out_path / fname
    with open(fp, "w", encoding="utf-8") as f:
        f.write(table_str)
    click.echo(f"Saved comparison to: {fp}")


if __name__ == "__main__":
    main()
