"""
Tests for 'springboot-tdd' skill.
Generated from benchmark case definitions for springboot-tdd.
"""

import ast
import base64
import glob
import json
import os
import py_compile
import re
import subprocess
import textwrap

import pytest

try:
    import yaml
except ModuleNotFoundError:
    yaml = None


class TestSpringbootTdd:
    """Verify the springboot-tdd skill output."""

    REPO_DIR = '/workspace/spring-petclinic'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestSpringbootTdd.REPO_DIR, rel)

    @staticmethod
    def _safe_read(path: str) -> str:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return fh.read()

    @staticmethod
    def _load_yaml(path: str):
        if yaml is None:
            pytest.skip("PyYAML not available")
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return yaml.safe_load(fh)

    @staticmethod
    def _load_json(path: str):
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return json.load(fh)

    @classmethod
    def _run_in_repo(cls, script: str, timeout: int = 120) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["python", "-c", textwrap.dedent(script)],
            cwd=cls.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    @classmethod
    def _run_cmd(cls, command, args=None, timeout=120):
        args = args or []
        if isinstance(command, str) and args:
            return subprocess.run(
                [command, *args],
                cwd=cls.REPO_DIR,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        return subprocess.run(
            command if isinstance(command, list) else command,
            cwd=cls.REPO_DIR,
            shell=isinstance(command, str),
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    @classmethod
    def _ensure_setup(cls, label, setup_cmds, fallback):
        if not setup_cmds:
            return
        key = tuple(setup_cmds)
        if key in cls._SETUP_CACHE:
            ok, msg = cls._SETUP_CACHE[key]
            if ok:
                return
            if fallback == "skip_if_setup_fails":
                pytest.skip(f"{label} setup failed: {msg}")
            pytest.fail(f"{label} setup failed: {msg}")
        for cmd in setup_cmds:
            r = subprocess.run(cmd, cwd=cls.REPO_DIR, shell=True,
                               capture_output=True, text=True, timeout=300)
            if r.returncode != 0:
                msg = (r.stderr or r.stdout or 'failed').strip()
                cls._SETUP_CACHE[key] = (False, msg)
                if fallback == "skip_if_setup_fails":
                    pytest.skip(f"{label} setup failed: {msg}")
                pytest.fail(f"{label} setup failed: {msg}")
        cls._SETUP_CACHE[key] = (True, 'ok')


    # ── file_path_check (static) ────────────────────────────────────────

    def test_appointment_entity_exists(self):
        """Verify Appointment entity and service source files exist"""
        _p = self._repo_path('src/main/java/org/springframework/samples/petclinic/appointment/Appointment.java')
        assert os.path.isfile(_p), f'Missing file: src/main/java/org/springframework/samples/petclinic/appointment/Appointment.java'
        _p = self._repo_path('src/main/java/org/springframework/samples/petclinic/appointment/AppointmentService.java')
        assert os.path.isfile(_p), f'Missing file: src/main/java/org/springframework/samples/petclinic/appointment/AppointmentService.java'

    def test_appointment_test_exists(self):
        """Verify test file exists"""
        _p = self._repo_path('src/test/java/org/springframework/samples/petclinic/appointment/AppointmentServiceTests.java')
        assert os.path.isfile(_p), f'Missing file: src/test/java/org/springframework/samples/petclinic/appointment/AppointmentServiceTests.java'

    # ── semantic_check (static) ────────────────────────────────────────

    def test_entity_jpa_annotations(self):
        """Verify @Entity and @Table annotations on Appointment class"""
        _p = self._repo_path('src/main/java/org/springframework/samples/petclinic/appointment/Appointment.java')
        assert os.path.exists(_p), f'Missing: src/main/java/org/springframework/samples/petclinic/appointment/Appointment.java'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert '@Entity' in _all, 'Missing: @Entity'
        assert '@Table' in _all, 'Missing: @Table'
        assert 'class Appointment' in _all, 'Missing: class Appointment'

    def test_future_date_validation(self):
        """Verify @Future annotation on date field"""
        _p = self._repo_path('src/main/java/org/springframework/samples/petclinic/appointment/Appointment.java')
        assert os.path.exists(_p), f'Missing: src/main/java/org/springframework/samples/petclinic/appointment/Appointment.java'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert '@Future' in _all, 'Missing: @Future'
        assert 'date' in _all, 'Missing: date'
        assert 'LocalDate' in _all, 'Missing: LocalDate'
        assert 'LocalDateTime' in _all, 'Missing: LocalDateTime'

    def test_appointment_status_enum(self):
        """Verify AppointmentStatus enum with 3 values"""
        _p = self._repo_path('src/main/java/org/springframework/samples/petclinic/appointment/Appointment.java')
        assert os.path.exists(_p), f'Missing: src/main/java/org/springframework/samples/petclinic/appointment/Appointment.java'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'SCHEDULED' in _all, 'Missing: SCHEDULED'
        assert 'CANCELLED' in _all, 'Missing: CANCELLED'
        assert 'COMPLETED' in _all, 'Missing: COMPLETED'
        assert 'AppointmentStatus' in _all, 'Missing: AppointmentStatus'
        assert 'enum' in _all, 'Missing: enum'

    def test_repository_extends_jpa(self):
        """Verify AppointmentRepository extends JpaRepository"""
        _p = self._repo_path('src/main/java/org/springframework/samples/petclinic/appointment/AppointmentRepository.java')
        assert os.path.exists(_p), f'Missing: src/main/java/org/springframework/samples/petclinic/appointment/AppointmentRepository.java'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'extends JpaRepository' in _all, 'Missing: extends JpaRepository'
        assert 'findByPet' in _all, 'Missing: findByPet'
        assert 'findByOwner' in _all, 'Missing: findByOwner'

    # ── functional_check ────────────────────────────────────────

    def test_maven_compiles(self):
        """Verify project compiles without errors"""
        result = self._run_cmd('./mvnw', args=['compile', '-q'], timeout=600)
        assert result.returncode == 0, (
            f'test_maven_compiles failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_schedule_appointment_success(self):
        """Verify scheduleAppointment with future date succeeds"""
        result = self._run_cmd('./mvnw', args=['test', '-Dtest=AppointmentServiceTests#testScheduleAppointmentSuccess', '-q'], timeout=600)
        assert result.returncode == 0, (
            f'test_schedule_appointment_success failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_past_date_rejected(self):
        """Verify scheduleAppointment with past date throws ConstraintViolationException"""
        result = self._run_cmd('./mvnw', args=['test', '-Dtest=AppointmentServiceTests#testPastDateRejected', '-q'], timeout=600)
        assert result.returncode == 0, (
            f'test_past_date_rejected failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_cancel_completed_throws(self):
        """Verify cancelAppointment of COMPLETED throws IllegalStateException"""
        result = self._run_cmd('./mvnw', args=['test', '-Dtest=AppointmentServiceTests#testCancelCompletedThrows', '-q'], timeout=600)
        assert result.returncode == 0, (
            f'test_cancel_completed_throws failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_cancel_scheduled_succeeds(self):
        """Verify cancelAppointment of SCHEDULED transitions to CANCELLED"""
        result = self._run_cmd('./mvnw', args=['test', '-Dtest=AppointmentServiceTests#testCancelScheduledSucceeds', '-q'], timeout=600)
        assert result.returncode == 0, (
            f'test_cancel_scheduled_succeeds failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_full_appointment_suite(self):
        """Run the full appointment test suite"""
        result = self._run_cmd('./mvnw', args=['test', '-Dtest=AppointmentServiceTests', '-q'], timeout=600)
        assert result.returncode == 0, (
            f'test_full_appointment_suite failed (exit {result.returncode})\n' + result.stderr[:500]
        )

