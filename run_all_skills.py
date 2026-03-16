#!/usr/bin/env python3
"""
Batch script to run all skills.

Usage:
    python run_all_skills.py                    # run all skills
    python run_all_skills.py --skip skill1,skill2  # skip specified skills
    python run_all_skills.py --only skill1,skill2  # run only specified skills
    python run_all_skills.py --resume            # resume from last interruption
    python run_all_skills.py --dry-run           # preview commands to run
"""

import argparse
import subprocess
import sys
import yaml
from pathlib import Path
from datetime import datetime
from typing import List, Set, Optional


class SkillRunner:
    """Batch skill executor"""

    def __init__(self, config_path: str = "config/benchmark_config.yaml"):
        self.config_path = Path(config_path)
        self.log_file = (
            Path("reports")
            / f"batch_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        self.completed_file = Path("reports") / ".batch_run_completed.txt"

        # Ensure reports directory exists
        self.log_file.parent.mkdir(exist_ok=True)

    def load_skills(self) -> List[str]:
        """Load all skill IDs from the config file"""
        if not self.config_path.exists():
            print(f"Error: config file not found: {self.config_path}")
            sys.exit(1)

        with open(self.config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        skills = config.get("skills", [])
        skill_ids = [skill["id"] for skill in skills if "id" in skill]

        print(f"Loaded {len(skill_ids)} skill(s) from config")
        return skill_ids

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
        self, skill_id: str, dry_run: bool = False, use_skill: Optional[bool] = None
    ) -> bool:
        """
        Run a single skill.

        Args:
            skill_id: skill ID
            dry_run: dry-run mode only

        Returns:
            bool: whether successful
        """
        cmd = ["python", "main.py", "run", "-s", skill_id]
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

    def run_all(
        self,
        skip_skills: Optional[List[str]] = None,
        only_skills: Optional[List[str]] = None,
        resume: bool = False,
        dry_run: bool = False,
        use_skill: Optional[bool] = None,
    ):
        """
        Run all skills in batch.

        Args:
            skip_skills: list of skill IDs to skip
            only_skills: run only these skill IDs
            resume: resume from last interruption
            dry_run: show commands only, do not execute
        """
        all_skills = self.load_skills()

        # Apply filters
        if only_skills:
            skills_to_run = [s for s in all_skills if s in only_skills]
            self.log(
                f"Running only {len(skills_to_run)} specified skill(s): {', '.join(skills_to_run)}"
            )
        else:
            skills_to_run = all_skills

        if skip_skills:
            skills_to_run = [s for s in skills_to_run if s not in skip_skills]
            self.log(f"Skipping {len(skip_skills)} skill(s): {', '.join(skip_skills)}")

        # Resume mode: skip completed skills
        if resume:
            completed = self.load_completed_skills()
            skills_to_run = [s for s in skills_to_run if s not in completed]
            self.log(
                f"Resume mode: {len(completed)} completed, {len(skills_to_run)} remaining"
            )

        if not skills_to_run:
            self.log("No skills to run")
            return

        # Run statistics
        total = len(skills_to_run)
        success_count = 0
        failed_count = 0
        failed_skills = []

        self.log(f"{'=' * 60}")
        self.log(f"Starting batch run of {total} skill(s)")
        self.log(f"Log file: {self.log_file}")
        self.log(f"{'=' * 60}")

        try:
            for idx, skill_id in enumerate(skills_to_run, 1):
                self.log(f"\n[{idx}/{total}] Running: {skill_id}")

                success = self.run_skill(skill_id, dry_run, use_skill)

                if success:
                    success_count += 1
                    if not dry_run:
                        self.save_completed_skill(skill_id)
                else:
                    failed_count += 1
                    failed_skills.append(skill_id)

                # Show progress
                self.log(
                    f"Progress: {idx}/{total} (succeeded: {success_count}, failed: {failed_count})"
                )

        except KeyboardInterrupt:
            self.log(f"\nBatch run interrupted by user")
            self.log(f"Completed: {success_count}/{total}")
            self.log(f"Use --resume to continue")
            sys.exit(1)

        # Final summary
        self.log(f"\n{'=' * 60}")
        self.log(f"Batch run complete")
        self.log(f"Total: {total}, succeeded: {success_count}, failed: {failed_count}")

        if failed_skills:
            self.log(f"\nFailed skills:")
            for skill_id in failed_skills:
                self.log(f"  - {skill_id}")

        self.log(f"{'=' * 60}")

        # Clear completion record file if all succeeded
        if not dry_run and failed_count == 0 and self.completed_file.exists():
            self.completed_file.unlink()


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
