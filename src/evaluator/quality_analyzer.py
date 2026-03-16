"""
Quality Analyzer - L3 quality-level analysis
Static analysis, code similarity, and safety checks.
"""

import re
import difflib
from typing import Dict, Any, List, Optional

from .base_evaluator import (
    BaseEvaluator,
    EvaluationLevel,
    EvaluationStatus,
    EvaluationResult,
)
from ..orchestrator.docker_manager import DockerManager
from ..orchestrator.logger import get_logger

logger = get_logger(__name__)


class QualityAnalyzer(BaseEvaluator):
    """
    L3: Static analysis check.

    Checks whether code contains required patterns/keywords.
    """

    @property
    def level(self) -> EvaluationLevel:
        return EvaluationLevel.L3

    @property
    def method(self) -> str:
        return "static_analysis"

    async def evaluate(self) -> EvaluationResult:
        """
        Run static analysis.

        Parameters:
            must_include: List of patterns that must be present
            must_not_include: List of patterns that must not be present
            target_files: List of files to check
            working_dir: Working directory
        """
        logger.info("Running static analysis")

        must_include = self.params.get("must_include", [])
        must_not_include = self.params.get("must_not_include", [])
        target_files = self.params.get("target_files", [])
        working_dir = self.params.get("working_dir", "/workspace")

        # If no files specified, get target files from preprocessing
        if not target_files:
            # Default: check all source files
            result = self.docker_manager.execute_command(
                f"find {working_dir} -name '*.cpp' -o -name '*.py' | head -20"
            )
            if result.exit_code == 0:
                target_files = [
                    f.replace(working_dir + "/", "")
                    for f in result.stdout.strip().split("\n")
                    if f
                ]

        # Collect analysis results
        missing_patterns = []
        forbidden_found = []
        checked_files = []

        for file_path in target_files:
            full_path = f"{working_dir}/{file_path}"

            # Read file content
            result = self.docker_manager.execute_command(f"cat {full_path}")
            if result.exit_code != 0:
                continue

            content = result.stdout
            checked_files.append(file_path)

            # Check must-include patterns
            for pattern in must_include:
                if not self._pattern_exists(content, pattern):
                    missing_patterns.append({"file": file_path, "pattern": pattern})

            # Check must-not-include patterns
            for pattern in must_not_include:
                if self._pattern_exists(content, pattern):
                    forbidden_found.append({"file": file_path, "pattern": pattern})

        # Compute score
        total_checks = len(must_include) + len(must_not_include)
        if total_checks == 0:
            return self._create_result(
                status=EvaluationStatus.SKIPPED,
                score=1.0,
                message="No patterns to check",
            )

        violations = len(missing_patterns) + len(forbidden_found)
        score = 1.0 - (violations / (total_checks * max(1, len(target_files))))
        score = max(0.0, score)

        if violations == 0:
            return self._create_result(
                status=EvaluationStatus.PASSED,
                score=1.0,
                message="All static analysis checks passed",
                details={
                    "checked_files": checked_files,
                    "must_include": must_include,
                    "must_not_include": must_not_include,
                },
            )
        else:
            messages = []
            if missing_patterns:
                messages.append(f"Missing {len(missing_patterns)} required pattern(s)")
            if forbidden_found:
                messages.append(f"Found {len(forbidden_found)} forbidden pattern(s)")

            return self._create_result(
                status=EvaluationStatus.FAILED,
                score=score,
                message="; ".join(messages),
                details={
                    "checked_files": checked_files,
                    "missing_patterns": missing_patterns[:10],
                    "forbidden_patterns": forbidden_found[:10],
                },
            )

    def _pattern_exists(self, content: str, pattern: str) -> bool:
        """Check whether a pattern exists in content."""
        try:
            # Try matching as a regular expression
            if re.search(pattern, content, re.MULTILINE):
                return True
        except re.error:
            # If not a valid regex, fall back to plain-string matching
            pass

        return pattern in content


class SimilarityAnalyzer(BaseEvaluator):
    """
    L3: Code similarity analysis.

    Compares modified code against the original version.
    """

    @property
    def level(self) -> EvaluationLevel:
        return EvaluationLevel.L3

    @property
    def method(self) -> str:
        return "similarity_analysis"

    async def evaluate(self) -> EvaluationResult:
        """
        Run similarity analysis.

        Parameters:
            min_similarity: Minimum similarity threshold (0.0-1.0)
            reference_dir: Reference code directory
            target_files: List of files to compare
            working_dir: Working directory
        """
        logger.info("Running similarity analysis")

        min_similarity = self.params.get("min_similarity", 0.8)
        reference_dir = self.params.get("reference_dir", "/tmp/golden_reference")
        target_files = self.params.get("target_files", [])
        working_dir = self.params.get("working_dir", "/workspace")

        if not target_files:
            # Get files from the reference directory
            result = self.docker_manager.execute_command(
                f"find {reference_dir} -type f -name '*.cpp' -o -name '*.py' | head -10"
            )
            if result.exit_code == 0:
                target_files = [
                    f.replace(reference_dir + "/", "")
                    for f in result.stdout.strip().split("\n")
                    if f
                ]

        similarities = []

        for file_path in target_files:
            ref_path = f"{reference_dir}/{file_path}"
            current_path = f"{working_dir}/{file_path}"

            # Read reference file
            ref_result = self.docker_manager.execute_command(f"cat {ref_path}")
            if ref_result.exit_code != 0:
                continue

            # Read current file
            current_result = self.docker_manager.execute_command(f"cat {current_path}")
            if current_result.exit_code != 0:
                continue

            # Compute similarity
            similarity = self._calculate_similarity(
                ref_result.stdout, current_result.stdout
            )

            similarities.append({"file": file_path, "similarity": round(similarity, 3)})

        if not similarities:
            return self._create_result(
                status=EvaluationStatus.SKIPPED,
                score=1.0,
                message="No files to compare",
            )

        # Compute average similarity
        avg_similarity = sum(s["similarity"] for s in similarities) / len(similarities)

        # Identify files below threshold
        low_similarity_files = [
            s for s in similarities if s["similarity"] < min_similarity
        ]

        if avg_similarity >= min_similarity and not low_similarity_files:
            return self._create_result(
                status=EvaluationStatus.PASSED,
                score=avg_similarity,
                message=f"Average similarity: {avg_similarity:.1%}",
                details={
                    "similarities": similarities,
                    "min_similarity": min_similarity,
                },
            )
        else:
            return self._create_result(
                status=EvaluationStatus.FAILED,
                score=avg_similarity,
                message=f"Similarity below threshold: {avg_similarity:.1%} < {min_similarity:.1%}",
                details={
                    "similarities": similarities,
                    "low_similarity_files": low_similarity_files,
                    "min_similarity": min_similarity,
                },
            )

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate the similarity between two text strings."""
        # Use difflib's SequenceMatcher
        matcher = difflib.SequenceMatcher(None, text1, text2)
        return matcher.ratio()


class SafetyChecker(BaseEvaluator):
    """
    L3: Safety check.

    Checks whether code contains unsafe patterns.
    """

    @property
    def level(self) -> EvaluationLevel:
        return EvaluationLevel.L3

    @property
    def method(self) -> str:
        return "safety_check"

    async def evaluate(self) -> EvaluationResult:
        """
        Run the safety check.

        Parameters:
            forbidden_patterns: List of forbidden patterns
            target_files: Files to check
            working_dir: Working directory
        """
        logger.info("Running safety check")

        forbidden_patterns = self.params.get("forbidden_patterns", [])
        target_files = self.params.get("target_files", [])
        working_dir = self.params.get("working_dir", "/workspace")

        if not forbidden_patterns:
            return self._create_result(
                status=EvaluationStatus.SKIPPED,
                score=1.0,
                message="No safety patterns defined",
            )

        # If no files specified, search the entire working directory
        violations = []

        for pattern in forbidden_patterns:
            # Use grep to search for the pattern
            cmd = f"grep -rn '{pattern}' {working_dir} --include='*.py' --include='*.cpp' 2>/dev/null | head -5"
            result = self.docker_manager.execute_command(cmd)

            if result.exit_code == 0 and result.stdout.strip():
                matches = result.stdout.strip().split("\n")
                violations.append(
                    {"pattern": pattern, "matches": matches[:3]}  # Limit match count
                )

        if not violations:
            return self._create_result(
                status=EvaluationStatus.PASSED,
                score=1.0,
                message="No safety violations found",
            )
        else:
            return self._create_result(
                status=EvaluationStatus.FAILED,
                score=0.0,
                message=f"Found {len(violations)} safety violation(s)",
                details={"violations": violations},
            )
