"""
Test for 'tdd-workflow' skill — TDD Workflow
Validates that the Agent implemented a discount calculator with proper TDD
approach including category, progressive, and tier discounts with test coverage.
"""

import os
import re
import subprocess

import pytest

from _dependency_utils import ensure_python_dependencies


@pytest.fixture(scope="module", autouse=True)
def _ensure_repo_dependencies():
    ensure_python_dependencies(TestTddWorkflow.REPO_DIR)


class TestTddWorkflow:
    """Verify TDD-based discount calculator implementation."""

    REPO_DIR = "/workspace/python"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    # ------------------------------------------------------------------
    # L1: File existence and syntax
    # ------------------------------------------------------------------

    def test_calculator_file_exists(self):
        """src/calculator.py must exist."""
        fpath = os.path.join(self.REPO_DIR, "src", "calculator.py")
        assert os.path.isfile(fpath), "src/calculator.py not found"

    def test_test_calculator_file_exists(self):
        """tests/test_calculator.py must exist."""
        fpath = os.path.join(self.REPO_DIR, "tests", "test_calculator.py")
        assert os.path.isfile(fpath), "tests/test_calculator.py not found"

    def test_calculator_module_compiles(self):
        """src/calculator.py must be syntactically valid Python."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "src/calculator.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert (
            result.returncode == 0
        ), f"src/calculator.py has syntax errors:\n{result.stderr}"

    def test_test_file_compiles(self):
        """tests/test_calculator.py must be syntactically valid Python."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "tests/test_calculator.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert (
            result.returncode == 0
        ), f"tests/test_calculator.py has syntax errors:\n{result.stderr}"

    # ------------------------------------------------------------------
    # L1: Calculator class structure
    # ------------------------------------------------------------------

    def test_calculator_class_defined(self):
        """src/calculator.py must define a Calculator (or similar) class."""
        content = self._read("src", "calculator.py")
        assert re.search(
            r"class\s+\w*[Cc]alculator", content
        ), "No Calculator class found in src/calculator.py"

    def test_calculator_accepts_items_and_tier(self):
        """Calculator must accept items and a customer tier parameter."""
        content = self._read("src", "calculator.py")
        # The class or its methods should reference items/cart AND tier
        has_items = bool(re.search(r"items|cart|order", content, re.IGNORECASE))
        has_tier = bool(
            re.search(r"tier|customer_tier|membership", content, re.IGNORECASE)
        )
        assert has_items, "Calculator does not appear to accept items/cart input"
        assert (
            has_tier
        ), "Calculator does not appear to accept a customer tier parameter"

    # ------------------------------------------------------------------
    # L1: Discount strategies present
    # ------------------------------------------------------------------

    def test_category_discount_logic_exists(self):
        """Calculator must contain logic for category-based discounts."""
        content = self._read("src", "calculator.py")
        assert re.search(
            r"category|categor", content, re.IGNORECASE
        ), "No category discount logic found in calculator.py"

    def test_progressive_discount_logic_exists(self):
        """Calculator must contain logic for volume/progressive discounts."""
        content = self._read("src", "calculator.py")
        patterns = [
            r"progressive",
            r"volume",
            r"threshold",
            r"quantity.*discount",
            r"discount.*quantity",
            r"tier.*quantity",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "No progressive/volume discount logic found in calculator.py"

    def test_tier_discount_logic_exists(self):
        """Calculator must contain logic for customer tier discounts."""
        content = self._read("src", "calculator.py")
        patterns = [
            r"gold",
            r"silver",
            r"regular",
            r"tier.*discount",
            r"customer.*tier",
            r"membership",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "No customer tier discount logic found in calculator.py"

    # ------------------------------------------------------------------
    # L2: Dynamic execution — agent's own tests pass
    # ------------------------------------------------------------------

    def test_agent_test_suite_passes(self):
        """The agent's test_calculator.py must pass when executed with pytest."""
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/test_calculator.py", "-v", "--tb=short"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert (
            result.returncode == 0
        ), f"Agent's test suite failed:\n{result.stdout[-3000:]}\n{result.stderr[-1000:]}"

    def test_agent_tests_have_sufficient_coverage(self):
        """The agent's test file must contain at least 5 test functions."""
        content = self._read("tests", "test_calculator.py")
        test_funcs = re.findall(r"def\s+(test_\w+)", content)
        assert len(test_funcs) >= 5, (
            f"test_calculator.py has only {len(test_funcs)} test functions — "
            f"need at least 5 for TDD coverage: {test_funcs}"
        )

    # ------------------------------------------------------------------
    # L2: Functional correctness — run calculator logic
    # ------------------------------------------------------------------

    def test_empty_cart_returns_zero_total(self):
        """An empty cart must return a total of 0."""
        script = (
            "import sys; sys.path.insert(0, 'src')\n"
            "from calculator import *\n"
            "# Try common class/function names\n"
            "calc = None\n"
            "for name in dir():\n"
            "    obj = eval(name)\n"
            "    if isinstance(obj, type) and 'calc' in name.lower():\n"
            "        try:\n"
            "            calc = obj()\n"
            "            break\n"
            "        except TypeError:\n"
            "            try:\n"
            "                calc = obj(tier='regular')\n"
            "                break\n"
            "            except: pass\n"
            "if calc is None:\n"
            "    print('NO_CALC_CLASS'); sys.exit(0)\n"
            "# Try calling with empty items\n"
            "for method in ['calculate', 'compute', 'total', 'get_total', 'calculate_total']:\n"
            "    fn = getattr(calc, method, None)\n"
            "    if fn:\n"
            "        try:\n"
            "            result = fn([])\n"
            "            print(f'TOTAL={result}')\n"
            "            sys.exit(0)\n"
            "        except: pass\n"
            "        try:\n"
            "            result = fn(items=[])\n"
            "            print(f'TOTAL={result}')\n"
            "            sys.exit(0)\n"
            "        except: pass\n"
            "print('NO_METHOD')\n"
        )
        result = subprocess.run(
            ["python", "-c", script],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout.strip()
        if "TOTAL=" in output:
            val = float(output.split("TOTAL=")[1].strip())
            assert val == 0.0, f"Empty cart should return 0, got {val}"

    def test_negative_price_rejected(self):
        """The calculator must reject items with negative prices."""
        script = (
            "import sys; sys.path.insert(0, 'src')\n"
            "from calculator import *\n"
            "calc = None\n"
            "for name in dir():\n"
            "    obj = eval(name)\n"
            "    if isinstance(obj, type) and 'calc' in name.lower():\n"
            "        try:\n"
            "            calc = obj()\n"
            "            break\n"
            "        except TypeError:\n"
            "            try:\n"
            "                calc = obj(tier='regular')\n"
            "                break\n"
            "            except: pass\n"
            "if calc is None:\n"
            "    print('SKIP'); sys.exit(0)\n"
            "item = {'price': -10, 'quantity': 1, 'category': 'general'}\n"
            "for method in ['calculate', 'compute', 'total', 'get_total', 'calculate_total']:\n"
            "    fn = getattr(calc, method, None)\n"
            "    if fn:\n"
            "        try:\n"
            "            fn([item])\n"
            "            print('NO_ERROR')  # Bad — should have raised\n"
            "            sys.exit(0)\n"
            "        except (ValueError, TypeError, Exception) as e:\n"
            "            print(f'REJECTED={type(e).__name__}')\n"
            "            sys.exit(0)\n"
            "print('SKIP')\n"
        )
        result = subprocess.run(
            ["python", "-c", script],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout.strip()
        if output == "NO_ERROR":
            pytest.fail("Calculator accepted a negative price without raising an error")

    def test_test_names_are_descriptive(self):
        """Each test function should have a descriptive name, not just test_1, test_2."""
        content = self._read("tests", "test_calculator.py")
        test_funcs = re.findall(r"def\s+(test_\w+)", content)
        generic_names = [n for n in test_funcs if re.match(r"test_\d+$", n)]
        assert (
            len(generic_names) == 0
        ), f"Test names should be descriptive, not generic: {generic_names}"
