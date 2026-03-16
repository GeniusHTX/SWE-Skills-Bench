"""
Base Evaluator - Evaluator base class
Defines the evaluation interface and common functionality.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum

from ..orchestrator.docker_manager import DockerManager
from ..orchestrator.logger import get_logger

logger = get_logger(__name__)


class EvaluationLevel(Enum):
    """Evaluation levels."""

    L1 = "L1"  # Build level
    L2 = "L2"  # Functional level
    L3 = "L3"  # Quality level


class EvaluationStatus(Enum):
    """Evaluation status values."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class EvaluationResult:
    """Evaluation result."""

    level: str
    method: str
    status: str
    score: float  # 0.0 - 1.0
    message: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def passed(self) -> bool:
        return self.status == EvaluationStatus.PASSED.value


class BaseEvaluator(ABC):
    """
    Evaluator base class.

    All evaluators must inherit from this class and implement the evaluate method.
    """

    def __init__(self, docker_manager: DockerManager, params: Dict[str, Any] = None):
        """
        Initialize.

        Args:
            docker_manager: Docker manager instance
            params: Evaluation parameters
        """
        self.docker_manager = docker_manager
        self.params = params or {}

    @property
    @abstractmethod
    def level(self) -> EvaluationLevel:
        """Evaluation level."""
        pass

    @property
    @abstractmethod
    def method(self) -> str:
        """Evaluation method name."""
        pass

    @abstractmethod
    async def evaluate(self) -> EvaluationResult:
        """
        Run the evaluation.

        Returns:
            EvaluationResult: Evaluation result
        """
        pass

    def _create_result(
        self,
        status: EvaluationStatus,
        score: float,
        message: str,
        details: Dict[str, Any] = None,
    ) -> EvaluationResult:
        """Create an evaluation result."""
        return EvaluationResult(
            level=self.level.value,
            method=self.method,
            status=status.value,
            score=score,
            message=message,
            details=details or {},
        )


class ModularEvaluator:
    """
    Modular evaluator.

    Manages and executes multiple evaluation plugins.
    """

    def __init__(
        self,
        docker_manager: DockerManager,
        skill_config: Dict[str, Any],
        global_config: Dict[str, Any],
    ):
        """
        Initialize.

        Args:
            docker_manager: Docker manager instance
            skill_config: Skill configuration
            global_config: Global configuration
        """
        self.docker_manager = docker_manager
        self.skill_config = skill_config
        self.global_config = global_config

        # Evaluator registry
        self.evaluator_registry: Dict[str, type] = {}
        self._register_default_evaluators()

    def _register_default_evaluators(self):
        """Register default evaluators."""
        from .build_checker import BuildChecker
        from .unit_test_runner import UnitTestRunner
        from .quality_analyzer import QualityAnalyzer, SimilarityAnalyzer, SafetyChecker

        self.evaluator_registry = {
            "build_check": BuildChecker,
            "unit_test": UnitTestRunner,
            "static_analysis": QualityAnalyzer,
            "similarity_analysis": SimilarityAnalyzer,
            "safety_check": SafetyChecker,
            "custom_script": CustomScriptEvaluator,
        }

    def register_evaluator(self, method: str, evaluator_class: type):
        """Register a custom evaluator."""
        self.evaluator_registry[method] = evaluator_class
        logger.debug(f"Registered evaluator: {method}")

    async def evaluate_all(self) -> Dict[str, Any]:
        """
        Run all evaluations.

        Returns:
            Dict: Aggregated evaluation results
        """
        logger.info("Starting evaluation")

        # Support two config locations:
        # 1) top-level `evaluation` in the skill config
        # 2) legacy: `evaluation` under `environment`
        # Load evaluation config (supports both locations)
        evaluation_configs = self.skill_config.get("evaluation", [])
        config_source = "skill"
        if not evaluation_configs:
            evaluation_configs = self.skill_config.get("environment", {}).get(
                "evaluation", []
            )
            config_source = "environment" if evaluation_configs else "none"

        logger.info(
            f"Loaded evaluation configs from: {config_source} (count={len(evaluation_configs)})"
        )
        results: List[EvaluationResult] = []

        for eval_config in evaluation_configs:
            # Check if enabled
            if not eval_config.get("enabled", True):
                logger.debug(
                    f"Skipping disabled evaluation: {eval_config.get('method')}"
                )
                continue

            level = eval_config.get("level", "L1")
            method = eval_config.get("method")
            params = eval_config.get("params", {})

            logger.info(f"Running evaluation: {level} - {method}")

            try:
                result = await self._run_single_evaluation(method, params)
                results.append(result)

                logger.info(
                    f"Evaluation result: {result.status} "
                    f"(score: {result.score:.2f})"
                )

            except Exception as e:
                logger.error(f"Evaluation failed: {e}")
                results.append(
                    EvaluationResult(
                        level=level,
                        method=method,
                        status=EvaluationStatus.ERROR.value,
                        score=0.0,
                        message=str(e),
                    )
                )

        # Aggregate results
        summary = self._summarize_results(results)

        logger.info(f"Evaluation completed: {summary['overall_status']}")
        return summary

    async def _run_single_evaluation(
        self, method: str, params: Dict[str, Any]
    ) -> EvaluationResult:
        """Run a single evaluation."""
        evaluator_class = self.evaluator_registry.get(method)

        if not evaluator_class:
            return EvaluationResult(
                level="unknown",
                method=method,
                status=EvaluationStatus.ERROR.value,
                score=0.0,
                message=f"Unknown evaluation method: {method}",
            )

        evaluator = evaluator_class(self.docker_manager, params)
        return await evaluator.evaluate()

    def _summarize_results(self, results: List[EvaluationResult]) -> Dict[str, Any]:
        """Summarize evaluation results."""
        total_score = 0.0
        passed_count = 0
        failed_count = 0

        level_scores = {
            "L1": {"score": 0.0, "count": 0, "passed": 0},
            "L2": {"score": 0.0, "count": 0, "passed": 0},
            "L3": {"score": 0.0, "count": 0, "passed": 0},
        }

        for result in results:
            total_score += result.score

            if result.passed:
                passed_count += 1
            else:
                failed_count += 1

            level = result.level
            if level in level_scores:
                level_scores[level]["score"] += result.score
                level_scores[level]["count"] += 1
                if result.passed:
                    level_scores[level]["passed"] += 1

        # Compute overall status
        if len(results) > 0:
            avg_score = total_score / len(results)
            overall_status = "passed" if failed_count == 0 else "failed"
        else:
            avg_score = 0.0
            overall_status = "no_evaluations"

        return {
            "overall_status": overall_status,
            "overall_score": round(avg_score, 3),
            "total_evaluations": len(results),
            "passed": passed_count,
            "failed": failed_count,
            "level_scores": {
                level: {
                    "average_score": (
                        round(data["score"] / data["count"], 3)
                        if data["count"] > 0
                        else 0
                    ),
                    "pass_rate": (
                        round(data["passed"] / data["count"], 3)
                        if data["count"] > 0
                        else 0
                    ),
                }
                for level, data in level_scores.items()
                if data["count"] > 0
            },
            "details": [r.to_dict() for r in results],
        }


class CustomScriptEvaluator(BaseEvaluator):
    """
    Custom script evaluator.

    Allows users to provide a custom evaluation script.
    """

    @property
    def level(self) -> EvaluationLevel:
        return EvaluationLevel.L3

    @property
    def method(self) -> str:
        return "custom_script"

    async def evaluate(self) -> EvaluationResult:
        """
        Run a custom evaluation script.

        Parameters:
            script: Script path (relative to workspace or absolute)
            args: Script argument list
            working_dir: Working directory
            timeout: Timeout in seconds
        """
        script = self.params.get("script", "")
        args = self.params.get("args", [])
        working_dir = self.params.get("working_dir", "/workspace")
        timeout = self.params.get("timeout", 300)

        if not script:
            return self._create_result(
                status=EvaluationStatus.SKIPPED,
                score=1.0,
                message="No custom script specified",
            )

        # Build command
        args_str = " ".join(str(a) for a in args)
        cmd = f"cd {working_dir} && python {script} {args_str}"

        logger.info(f"Running custom evaluation script: {script}")
        result = self.docker_manager.execute_command(cmd, timeout=timeout)

        if result.exit_code == 0:
            # Try to parse score from output
            score = self._parse_score_from_output(result.stdout)
            return self._create_result(
                status=EvaluationStatus.PASSED,
                score=score,
                message="Custom evaluation passed",
                details={
                    "script": script,
                    "output": result.stdout[:2000] if result.stdout else "",
                },
            )
        else:
            return self._create_result(
                status=EvaluationStatus.FAILED,
                score=0.0,
                message=f"Custom evaluation failed with exit code {result.exit_code}",
                details={
                    "script": script,
                    "exit_code": result.exit_code,
                    "output": result.stdout[:2000] if result.stdout else "",
                    "error": result.stderr[:2000] if result.stderr else "",
                },
            )

    def _parse_score_from_output(self, output: str) -> float:
        """Try to parse a score value from output."""
        import re

        # Look for patterns like "score: 0.95" or "SCORE=0.95"
        patterns = [
            r"score[:\s=]+([0-9.]+)",
            r"pass[_\s]?rate[:\s=]+([0-9.]+)",
            r"accuracy[:\s=]+([0-9.]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                try:
                    score = float(match.group(1))
                    return min(1.0, max(0.0, score))
                except ValueError:
                    pass

        # Default: return 1.0 (passed)
        return 1.0
