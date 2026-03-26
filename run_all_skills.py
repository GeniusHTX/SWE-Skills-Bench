#!/usr/bin/env python3
"""
Batch script to run all skills across all configured batches.

Iterates over global.batches in the config file, writes a temporary config
per batch (with active_batch overridden), and invokes main.py for each skill.
Progress logs and resume state are stored per model/batch under reports/.

Usage:
    python run_all_skills.py                          # run all skills in all batches
    python run_all_skills.py --skip skill1,skill2     # skip specified skills
    python run_all_skills.py --only skill1,skill2     # run only specified skills
    python run_all_skills.py --resume                 # resume from last interruption (per batch)
    python run_all_skills.py --dry-run                # preview commands to run
    python run_all_skills.py --config path/to/cfg     # use a custom config file
    python run_all_skills.py --no-use-skill           # disable skill injection
"""

import argparse
import subprocess
import sys
import os
import re
import yaml
from pathlib import Path
from datetime import datetime
from typing import List, Set, Optional

from dotenv import load_dotenv

load_dotenv()


def _get_model_name() -> str:
    """Get sanitized model name from ANTHROPIC_DEFAULT_SONNET_MODEL env var."""
    raw = os.environ.get("ANTHROPIC_DEFAULT_SONNET_MODEL", "unknown-model")
    return re.sub(r"[^A-Za-z0-9._-]+", "-", raw) or "unknown-model"


class SkillRunner:
    """Batch skill executor"""

    def __init__(self, config_path: str = "config/benchmark_config.yaml"):
        self.config_path = Path(config_path)
        self.model_name = _get_model_name()
        # Per-batch state — initialized by _setup_batch_dirs inside run_all_for_batch
        self.log_file: Optional[Path] = None
        self.completed_file: Optional[Path] = None

    def _load_config(self) -> dict:
        """Load and return the benchmark YAML config."""
        if not self.config_path.exists():
            print(f"Error: config file not found: {self.config_path}")
            sys.exit(1)
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _get_batches(self, config: dict) -> List[str]:
        """Return the list of batch names from config global.batches."""
        return [str(b) for b in config.get("global", {}).get("batches", [])]

    def _setup_batch_dirs(self, batch_name: str):
        """Create per-batch report/log directory and set log_file/completed_file."""
        reports_dir = Path("reports") / self.model_name / batch_name
        reports_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = reports_dir / f"batch_run_{ts}.log"
        self.completed_file = reports_dir / ".batch_run_completed.txt"

    def _write_temp_config(self, config: dict, batch_name: str) -> Path:
        """Write a temporary YAML config with active_batch overridden to batch_name."""
        import copy

        cfg = copy.deepcopy(config)
        cfg.setdefault("global", {})["active_batch"] = batch_name
        tmp_path = Path(f"_tmp_config_{batch_name}.yaml")
        with open(tmp_path, "w", encoding="utf-8") as f:
            yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False)
        return tmp_path

    def load_skills(self, config: dict) -> List[str]:
        """Return all skill IDs from an already-loaded config dict."""
        return [s["id"] for s in config.get("skills", []) if "id" in s]

    def load_completed_skills(self) -> Set[str]:
        """Load completed skill IDs"""
        if not self.completed_file.exists():
            return set()

        with open(self.completed_file, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())

    def save_completed_skill(self, skill_id: str):
        """Save a completed skill ID"""
        with open(self.completed_file, "a", encoding="utf-8") as f:
            f.write(f"{skill_id}\n")

    def log(self, message: str):
        """Log a message"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_message + "\n")

    def run_skill(
        self,
        skill_id: str,
        config_file: Path,
        dry_run: bool = False,
        use_skill: Optional[bool] = None,
    ) -> bool:
        """
        Run a single skill using the specified batch config file.

        Args:
            skill_id: skill ID
            config_file: path to the per-batch temp config YAML
            dry_run: dry-run mode only

        Returns:
            bool: whether successful
        """
        cmd = ["python", "main.py", "run", "-s", skill_id, "--config", str(config_file)]
        if use_skill is True:
            cmd.append("--use-skill")
        elif use_skill is False:
            cmd.append("--no-use-skill")
        cmd_str = " ".join(cmd)

        self.log(f"{('[DRY-RUN] ' if dry_run else '')}Running: {cmd_str}")

        if dry_run:
            return True

        try:
            result = subprocess.run(
                cmd, capture_output=False, text=True  # print directly to terminal
            )

            if result.returncode == 0:
                self.log(f"\u2713 {skill_id} completed")
                return True
            else:
                self.log(f"\u2717 {skill_id} failed (exit code: {result.returncode})")
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
        skip_skills: Optional[List[str]] = None,
        only_skills: Optional[List[str]] = None,
        resume: bool = False,
        dry_run: bool = False,
        use_skill: Optional[bool] = None,
    ):
        """Run all skills for a single batch."""
        self._setup_batch_dirs(batch_name)
        tmp_config = self._write_temp_config(config, batch_name)

        try:
            skills_to_run = list(all_skills)
            if only_skills:
                skills_to_run = [s for s in skills_to_run if s in only_skills]
                self.log(
                    f"[{batch_name}] Running only {len(skills_to_run)} specified skill(s)"
                )
            if skip_skills:
                skills_to_run = [s for s in skills_to_run if s not in skip_skills]
                self.log(f"[{batch_name}] Skipping {len(skip_skills)} skill(s)")
            if resume:
                completed = self.load_completed_skills()
                skills_to_run = [s for s in skills_to_run if s not in completed]
                self.log(
                    f"[{batch_name}] Resume: {len(completed)} completed, {len(skills_to_run)} remaining"
                )

            if not skills_to_run:
                self.log(f"[{batch_name}] No skills to run")
                return

            total = len(skills_to_run)
            success_count = 0
            failed_count = 0
            failed_skills: List[str] = []

            self.log(f"{'=' * 60}")
            self.log(f"[{batch_name}] Starting batch run of {total} skill(s)")
            self.log(f"Log file: {self.log_file}")
            self.log(f"{'=' * 60}")

            try:
                for idx, skill_id in enumerate(skills_to_run, 1):
                    self.log(f"\n[{idx}/{total}] [{batch_name}] Running: {skill_id}")
                    success = self.run_skill(skill_id, tmp_config, dry_run, use_skill)
                    if success:
                        success_count += 1
                        if not dry_run:
                            self.save_completed_skill(skill_id)
                    else:
                        failed_count += 1
                        failed_skills.append(skill_id)
                    self.log(
                        f"Progress: {idx}/{total} (succeeded: {success_count}, failed: {failed_count})"
                    )
            except KeyboardInterrupt:
                self.log(f"\n[{batch_name}] Interrupted by user")
                self.log(f"Completed: {success_count}/{total}")
                self.log(f"Use --resume to continue")
                sys.exit(1)

            self.log(f"\n{'=' * 60}")
            self.log(f"[{batch_name}] Batch run complete")
            self.log(
                f"Total: {total}, succeeded: {success_count}, failed: {failed_count}"
            )
            if failed_skills:
                self.log(f"\nFailed skills:")
                for s in failed_skills:
                    self.log(f"  - {s}")
            self.log(f"{'=' * 60}")

            if not dry_run and failed_count == 0 and self.completed_file.exists():
                self.completed_file.unlink()
        finally:
            if tmp_config.exists():
                tmp_config.unlink()

    def run_all(
        self,
        skip_skills: Optional[List[str]] = None,
        only_skills: Optional[List[str]] = None,
        resume: bool = False,
        dry_run: bool = False,
        use_skill: Optional[bool] = None,
    ):
        """Run all skills across all configured batches."""
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
                skip_skills=skip_skills,
                only_skills=only_skills,
                resume=resume,
                dry_run=dry_run,
                use_skill=use_skill,
            )


def main():
    parser = argparse.ArgumentParser(
        description="Run all skills in batch",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_all_skills.py                           # run all skills
  python run_all_skills.py --skip add-uint-support   # skip a skill
  python run_all_skills.py --only skill1,skill2      # run only specified skills
  python run_all_skills.py --resume                  # resume from last interruption
  python run_all_skills.py --dry-run                 # preview commands
        """,
    )

    parser.add_argument("--skip", type=str, help="Skill IDs to skip (comma-separated)")

    parser.add_argument(
        "--only", type=str, help="Run only these skill IDs (comma-separated)"
    )

    parser.add_argument(
        "--resume", action="store_true", help="Resume from last interruption"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry-run mode (show commands, do not execute)",
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--use-skill",
        dest="use_skill",
        action="store_true",
        help="Copy local skills/ into the container (maps to main.py --use-skill)",
    )
    group.add_argument(
        "--no-use-skill",
        dest="use_skill",
        action="store_false",
        help="Do not copy local skills/ into the container (maps to main.py --no-use-skill)",
    )
    parser.set_defaults(use_skill=None)

    parser.add_argument(
        "--config",
        type=str,
        default="config/benchmark_config.yaml",
        help="Config file path (default: config/benchmark_config.yaml)",
    )

    args = parser.parse_args()

    # Parse args
    skip_skills = args.skip.split(",") if args.skip else None
    only_skills = args.only.split(",") if args.only else None

    # Create runner and execute
    runner = SkillRunner(config_path=args.config)
    runner.run_all(
        skip_skills=skip_skills,
        only_skills=only_skills,
        resume=args.resume,
        dry_run=args.dry_run,
        use_skill=args.use_skill,
    )


if __name__ == "__main__":
    main()
