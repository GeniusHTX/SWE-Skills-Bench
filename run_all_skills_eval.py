#!/usr/bin/env python3
"""
Reads the skill list from config/benchmark_config.yaml and runs each skill
via `python eval.py -s <skill-id> --use-skill`.

Usage:
  python run_all_skills_eval.py           # run all skills
  python run_all_skills_eval.py --dry-run # only show commands to execute
  python run_all_skills_eval.py --skip a,b # skip a and b
  python run_all_skills_eval.py --only a,b # run only a and b
"""

import argparse
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Optional

try:
    import yaml
except Exception:
    print("Please install dependencies first: pip install pyyaml")
    raise


class EvalBatchRunner:
    def __init__(self, config_path: str = "config/benchmark_config.yaml"):
        self.config_path = Path(config_path)
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
        self.log_file = (
            self.reports_dir
            / f"run_all_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )

    def load_skills(self) -> List[str]:
        if not self.config_path.exists():
            print(f"Config file not found: {self.config_path}")
            sys.exit(1)

        with open(self.config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        skills = cfg.get("skills", [])
        ids = [s.get("id") for s in skills if s.get("id")]
        print(f"Loaded {len(ids)} skill(s) from config")
        return ids

    def log(self, msg: str):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {msg}"
        print(line)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def run_skill(
        self,
        skill_id: str,
        dry_run: bool = False,
        use_skill: bool = True,
        use_agent: bool = True,
    ) -> bool:
        cmd = [sys.executable, "eval.py", "-s", skill_id]

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

    def run_all(
        self,
        skip: Optional[List[str]] = None,
        only: Optional[List[str]] = None,
        dry_run: bool = False,
        use_skill: bool = True,
        use_agent: bool = True,
    ):
        all_ids = self.load_skills()

        if only:
            to_run = [s for s in all_ids if s in only]
            self.log(f"Running only {len(to_run)} skill(s): {', '.join(to_run)}")
        else:
            to_run = all_ids

        if skip:
            to_run = [s for s in to_run if s not in skip]
            self.log(f"Skipping {len(skip)} skill(s)")

        if not to_run:
            self.log("No skills to run")
            return

        total = len(to_run)
        succ = 0
        fail = 0

        for idx, sid in enumerate(to_run, 1):
            self.log(f"[{idx}/{total}] Starting: {sid}")
            ok = self.run_skill(
                sid,
                dry_run=dry_run,
                use_skill=use_skill,
                use_agent=use_agent,
            )
            if ok:
                succ += 1
            else:
                fail += 1
            self.log(f"Progress: {idx}/{total} (succeeded {succ}, failed {fail})")

        self.log(f"Done: total {total}, succeeded {succ}, failed {fail}")


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
