#!/usr/bin/env python3
"""
Batch evaluation script: runs eval.py for each skill across all configured batches.

Iterates over global.batches in the config file, writes a temporary config
per batch (with active_batch overridden), and invokes eval.py for each skill.
Logs are stored per model/batch under reports/.

Usage:
  python run_all_skills_eval.py                      # run all skills in all batches
  python run_all_skills_eval.py --dry-run            # only show commands to execute
  python run_all_skills_eval.py --skip a,b           # skip a and b
  python run_all_skills_eval.py --only a,b           # run only a and b
  python run_all_skills_eval.py --config path/to/cfg # use a custom config file
  python run_all_skills_eval.py --no-use-skill       # disable skill injection
  python run_all_skills_eval.py --no-use-agent       # disable agent mode
"""

import argparse
import subprocess
import sys
import os
import re
from pathlib import Path
from datetime import datetime
from typing import List, Optional

try:
    import yaml
except Exception:
    print("Please install dependencies first: pip install pyyaml")
    raise

from dotenv import load_dotenv

load_dotenv()


def _get_model_name() -> str:
    """Get sanitized model name from ANTHROPIC_DEFAULT_SONNET_MODEL env var."""
    raw = os.environ.get("ANTHROPIC_DEFAULT_SONNET_MODEL", "unknown-model")
    return re.sub(r"[^A-Za-z0-9._-]+", "-", raw) or "unknown-model"


class EvalBatchRunner:
    def __init__(self, config_path: str = "config/benchmark_config.yaml"):
        self.config_path = Path(config_path)
        self.model_name = _get_model_name()
        # Per-batch state — initialized by _setup_batch_dirs inside run_all_for_batch
        self.log_file: Optional[Path] = None

    def _load_config(self) -> dict:
        """Load and return the benchmark YAML config."""
        if not self.config_path.exists():
            print(f"Config file not found: {self.config_path}")
            sys.exit(1)
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _get_batches(self, config: dict) -> List[str]:
        """Return the list of batch names from config global.batches."""
        return [str(b) for b in config.get("global", {}).get("batches", [])]

    def _setup_batch_dirs(self, batch_name: str):
        """Create per-batch report/log directory and set log_file."""
        reports_dir = Path("reports") / self.model_name / batch_name
        reports_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = reports_dir / f"run_all_eval_{ts}.log"

    def _write_temp_config(self, config: dict, batch_name: str) -> Path:
        """Write a temporary YAML config with active_batch overridden to batch_name."""
        import copy

        cfg = copy.deepcopy(config)
        cfg.setdefault("global", {})["active_batch"] = batch_name
        tmp_path = Path(f"_tmp_eval_config_{batch_name}.yaml")
        with open(tmp_path, "w", encoding="utf-8") as f:
            yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False)
        return tmp_path

    def load_skills(self, config: dict) -> List[str]:
        """Return all skill IDs from an already-loaded config dict."""
        return [s.get("id") for s in config.get("skills", []) if s.get("id")]

    def log(self, msg: str):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {msg}"
        print(line)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def run_skill(
        self,
        skill_id: str,
        config_file: Path,
        dry_run: bool = False,
        use_skill: bool = True,
        use_agent: bool = True,
    ) -> bool:
        cmd = [sys.executable, "eval.py", "-s", skill_id, "--config", str(config_file)]

        # use-skill / no-use-skill
        cmd.append("--use-skill" if use_skill else "--no-use-skill")

        # use-agent / no-use-agent
        cmd.append("--use-agent" if use_agent else "--no-use-agent")

        # No longer forwarding clean-container/output/log-level

        cmd_str = " ".join(cmd)
        self.log(f"{('[DRY-RUN] ' if dry_run else '')}Executing: {cmd_str}")

        if dry_run:
            return True

        try:
            res = subprocess.run(cmd, check=False)
            if res.returncode == 0:
                self.log(f"\u2713 {skill_id} succeeded")
                return True
            else:
                self.log(f"\u2717 {skill_id} failed (exit code {res.returncode})")
                return False
        except KeyboardInterrupt:
            self.log("Interrupted by user")
            raise
        except Exception as e:
            self.log(f"\u2717 {skill_id} exception: {e}")
            return False

    def run_all_for_batch(
        self,
        batch_name: str,
        config: dict,
        all_skills: List[str],
        skip: Optional[List[str]] = None,
        only: Optional[List[str]] = None,
        dry_run: bool = False,
        use_skill: bool = True,
        use_agent: bool = True,
    ):
        """Run evaluation for all skills in a single batch."""
        self._setup_batch_dirs(batch_name)
        tmp_config = self._write_temp_config(config, batch_name)

        try:
            to_run = list(all_skills)
            if only:
                to_run = [s for s in to_run if s in only]
                self.log(
                    f"[{batch_name}] Running only {len(to_run)} specified skill(s)"
                )
            if skip:
                to_run = [s for s in to_run if s not in skip]
                self.log(f"[{batch_name}] Skipping {len(skip)} skill(s)")

            if not to_run:
                self.log(f"[{batch_name}] No skills to evaluate")
                return

            total = len(to_run)
            succ = 0
            fail = 0

            self.log(f"{'=' * 60}")
            self.log(f"[{batch_name}] Starting eval run of {total} skill(s)")
            self.log(f"Log file: {self.log_file}")
            self.log(f"{'=' * 60}")

            for idx, sid in enumerate(to_run, 1):
                self.log(f"\n[{idx}/{total}] [{batch_name}] Evaluating: {sid}")
                ok = self.run_skill(
                    sid,
                    tmp_config,
                    dry_run=dry_run,
                    use_skill=use_skill,
                    use_agent=use_agent,
                )
                if ok:
                    succ += 1
                else:
                    fail += 1
                self.log(f"Progress: {idx}/{total} (succeeded {succ}, failed {fail})")

            self.log(f"\n{'=' * 60}")
            self.log(
                f"[{batch_name}] Done: total {total}, succeeded {succ}, failed {fail}"
            )
            self.log(f"{'=' * 60}")
        finally:
            if tmp_config.exists():
                tmp_config.unlink()

    def run_all(
        self,
        skip: Optional[List[str]] = None,
        only: Optional[List[str]] = None,
        dry_run: bool = False,
        use_skill: bool = True,
        use_agent: bool = True,
    ):
        """Run evaluation across all configured batches."""
        config = self._load_config()
        batches = self._get_batches(config)
        if not batches:
            print("Error: no batches defined in config global.batches")
            sys.exit(1)

        all_skills = self.load_skills(config)
        print(
            f"Loaded {len(all_skills)} skill(s) across {len(batches)} batch(es): {batches}"
        )

        for batch_name in batches:
            self.run_all_for_batch(
                batch_name=batch_name,
                config=config,
                all_skills=all_skills,
                skip=skip,
                only=only,
                dry_run=dry_run,
                use_skill=use_skill,
                use_agent=use_agent,
            )


def main():
    parser = argparse.ArgumentParser(
        description="Batch-run skills in config using eval.py"
    )
    parser.add_argument("--skip", type=str, help="Skill IDs to skip, comma-separated")
    parser.add_argument(
        "--only", type=str, help="Run only these skill IDs, comma-separated"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/benchmark_config.yaml",
        help="Config file path",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Only show commands to execute"
    )
    # Arguments passed to eval.py (consistent with Click options in eval.py)
    parser.add_argument(
        "--use-skill",
        dest="use_skill",
        action="store_true",
        help="Enable skill in the container (default)",
    )
    parser.add_argument(
        "--no-use-skill",
        dest="use_skill",
        action="store_false",
        help="Disable skill in the container",
    )
    parser.set_defaults(use_skill=True)

    parser.add_argument(
        "--use-agent",
        dest="use_agent",
        action="store_true",
        help="Enable agent in the container (default)",
    )
    parser.add_argument(
        "--no-use-agent",
        dest="use_agent",
        action="store_false",
        help="Disable agent in the container",
    )
    parser.set_defaults(use_agent=True)

    # No longer providing --clean-container/--output/--log-level options (these are handled internally by eval.py defaults)

    args = parser.parse_args()

    skip = args.skip.split(",") if args.skip else None
    only = args.only.split(",") if args.only else None

    runner = EvalBatchRunner(config_path=args.config)
    runner.run_all(
        skip=skip,
        only=only,
        dry_run=args.dry_run,
        use_skill=args.use_skill,
        use_agent=args.use_agent,
    )


if __name__ == "__main__":
    main()
