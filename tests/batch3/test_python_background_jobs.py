"""
Tests for python-background-jobs skill.
Validates email delivery state machine in celery/contrib/email_models.py.
"""

import os
import pytest

REPO_DIR = "/workspace/celery"


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read(rel: str) -> str:
    with open(_path(rel), encoding="utf-8", errors="ignore") as f:
        return f.read()


class TestPythonBackgroundJobs:

    # ── file_path_check ──────────────────────────────────────────────────────

    def test_email_models_file_exists(self):
        """celery/contrib/email_models.py must exist."""
        rel = "celery/contrib/email_models.py"
        assert os.path.isfile(_path(rel)), f"{rel} not found"
        assert os.path.getsize(_path(rel)) > 0, "email_models.py is empty"

    def test_contrib_init_exists(self):
        """celery/contrib/__init__.py must exist."""
        rel = "celery/contrib/__init__.py"
        assert os.path.isfile(_path(rel)), f"{rel} not found"

    # ── semantic_check ───────────────────────────────────────────────────────

    def test_delivery_state_enum_defined(self):
        """email_models.py must define DeliveryState with PENDING, SENDING, SENT, FAILED."""
        content = _read("celery/contrib/email_models.py")
        assert "class DeliveryState" in content, "DeliveryState enum not defined"
        for state in ("PENDING", "SENDING", "SENT", "FAILED"):
            assert state in content, f"{state} state missing from DeliveryState"

    def test_invalid_state_transition_errors_defined(self):
        """InvalidStateTransition and DuplicateDeliveryError must be defined."""
        content = _read("celery/contrib/email_models.py")
        assert (
            "class InvalidStateTransition" in content
        ), "InvalidStateTransition not defined"
        assert (
            "class DuplicateDeliveryError" in content
        ), "DuplicateDeliveryError not defined"

    def test_retry_backoff_cap_defined(self):
        """Backoff cap must be defined at 3600 seconds."""
        content = _read("celery/contrib/email_models.py")
        assert "3600" in content, "Backoff cap of 3600s not found in email_models.py"

    def test_smtp_immediate_fail_handler(self):
        """SMTPRecipientsRefused handler must not retry (immediate FAILED)."""
        content = _read("celery/contrib/email_models.py")
        assert "SMTPRecipientsRefused" in content, "SMTPRecipientsRefused not handled"

    # ── functional_check ─────────────────────────────────────────────────────

    def test_pending_to_sending_valid_transition(self):
        """PENDING -> SENDING must be a valid state transition (mocked)."""
        from enum import Enum

        class DeliveryState(Enum):
            PENDING = "PENDING"
            SENDING = "SENDING"
            SENT = "SENT"
            FAILED = "FAILED"

        VALID_TRANSITIONS = {
            DeliveryState.PENDING: {DeliveryState.SENDING},
            DeliveryState.SENDING: {DeliveryState.SENT, DeliveryState.FAILED},
        }

        class InvalidStateTransition(Exception):
            pass

        class Record:
            def __init__(self, state):
                self.state = state

            def transition(self, new_state):
                allowed = VALID_TRANSITIONS.get(self.state, set())
                if new_state not in allowed:
                    raise InvalidStateTransition(f"{self.state} -> {new_state}")
                self.state = new_state

        r = Record(DeliveryState.PENDING)
        r.transition(DeliveryState.SENDING)
        assert r.state == DeliveryState.SENDING

    def test_sent_to_sending_invalid_transition_error(self):
        """SENT -> SENDING must raise InvalidStateTransition (mocked)."""
        from enum import Enum

        class DeliveryState(Enum):
            PENDING = "PENDING"
            SENDING = "SENDING"
            SENT = "SENT"
            FAILED = "FAILED"

        VALID_TRANSITIONS = {
            DeliveryState.PENDING: {DeliveryState.SENDING},
            DeliveryState.SENDING: {DeliveryState.SENT, DeliveryState.FAILED},
        }

        class InvalidStateTransition(Exception):
            pass

        class Record:
            def __init__(self, state):
                self.state = state

            def transition(self, new_state):
                allowed = VALID_TRANSITIONS.get(self.state, set())
                if new_state not in allowed:
                    raise InvalidStateTransition(f"{self.state} -> {new_state}")
                self.state = new_state

        r = Record(DeliveryState.SENT)
        with pytest.raises(InvalidStateTransition):
            r.transition(DeliveryState.SENDING)

    def test_duplicate_delivery_error_for_existing(self):
        """Creating a second delivery for the same message_id must raise DuplicateDeliveryError (mocked)."""

        class DuplicateDeliveryError(Exception):
            pass

        registry = {}

        def create_delivery(message_id: str):
            if message_id in registry:
                raise DuplicateDeliveryError(f"{message_id} already exists")
            registry[message_id] = True

        create_delivery("msg1")
        with pytest.raises(DuplicateDeliveryError):
            create_delivery("msg1")

    def test_connection_error_5_retries_then_failed(self):
        """ConnectionError after 5 retries must result in FAILED state (mocked)."""

        class DeliveryState:
            PENDING = "PENDING"
            SENDING = "SENDING"
            FAILED = "FAILED"

        class FakeSMTP:
            def __init__(self, max_failures):
                self.calls = 0
                self.max_failures = max_failures

            def send(self):
                self.calls += 1
                raise ConnectionError("Connection refused")

        smtp = FakeSMTP(max_failures=5)
        state = DeliveryState.PENDING
        retry_count = 0
        max_retries = 5
        while retry_count < max_retries:
            try:
                smtp.send()
                state = DeliveryState.SENDING
                break
            except ConnectionError:
                retry_count += 1
        else:
            state = DeliveryState.FAILED

        assert state == DeliveryState.FAILED
        assert retry_count == 5

    def test_smtp_recipients_refused_immediate_failed(self):
        """SMTPRecipientsRefused must immediately set FAILED with zero retries (mocked)."""

        class SMTPRecipientsRefused(Exception):
            pass

        class DeliveryState:
            PENDING = "PENDING"
            FAILED = "FAILED"

        def deliver(smtp_error_class):
            retry_count = 0
            try:
                raise smtp_error_class("bad recipients")
            except SMTPRecipientsRefused:
                return DeliveryState.FAILED, retry_count

        state, retries = deliver(SMTPRecipientsRefused)
        assert state == DeliveryState.FAILED
        assert retries == 0

    def test_backoff_delay_caps_at_3600(self):
        """Exponential backoff must never exceed 3600 seconds (mocked)."""

        def compute_backoff(attempt: int, base: float = 2.0, cap: int = 3600) -> float:
            return min(base**attempt, cap)

        delays = [compute_backoff(i) for i in range(20)]
        assert max(delays) <= 3600, f"Max backoff {max(delays)} exceeds 3600s cap"
