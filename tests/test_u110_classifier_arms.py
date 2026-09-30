"""Cycle-12 U110 pins: errno-PROSE vocabulary + the zero-exit fall-through.

Assess findings F5/F6 (probe-verified at base aa93a57):

* F5 — tools print ``strerror`` prose (``Connection refused``, ``No space
  left on device``); the classifier only saw the symbolic log constants
  (``ECONNREFUSED``, ``ENOSPC``), so those reports classified non-error.
* F6 — wrapper asymmetry: ``{"code": 200, "stdout": "payment failed"}``
  and the bare text both classified failure, while ``{"code": 0, …}`` with
  the SAME text returned success because the zero exit short-circuited
  before the text scan.

Pins are behavioral: realistic payload/record shapes through the public
predicate and the record-level classifier, never pattern-echoes of the
regex (the tautology rule, cycle-11 review finding 1).
"""

import json

import pytest

from hermes_curator_evolver.candidates import _is_tool_failure, looks_like_error

# --- F5: errno prose, wrapped and bare -------------------------------------

_ERRNO_PROSE = [
    "Connection refused while fetching upstream",
    "curl failed: connection reset by peer",
    "write failed: no space left on device",
    "open /etc/app.conf: no such file or directory",
    "send: network is unreachable",
    "dial: host is unreachable",
    "getaddrinfo: name or service not known",
    "DNS: temporary failure in name resolution",
    "write error: broken pipe",
    "remount: read-only file system",
    "fork: cannot allocate memory",
]


@pytest.mark.parametrize("text", _ERRNO_PROSE)
def test_u110_errno_prose_classifies_failure(text):
    assert _is_tool_failure({}, text) is True


@pytest.mark.parametrize(
    "payload",
    [
        {"code": 0, "stdout": "fetch failed: connection refused"},
        {"exit_code": 0, "stderr": "no space left on device"},
        {"returncode": 0, "output": "no such file or directory"},
    ],
)
def test_u110_errno_prose_survives_a_zero_exit_wrapper(payload):
    assert looks_like_error(payload) is True


# --- F6: the zero-exit fall-through -----------------------------------------

_U110_CODE_ZERO_CASES = [
    # failure text decides the verdict with a wrapper zero, exactly as it
    # already did unwrapped and under an in-band HTTP code
    ({"code": 0, "stdout": "payment failed"}, True),
    ({"code": 200, "stdout": "payment failed"}, True),
    ("payment failed", True),
    # success-shaped and neutral text stay success under a zero exit
    ({"exit_code": 0, "stderr": "warnings printed, nothing failed"}, False),
    ({"exit_code": 0, "stdout": "3 passed, no errors found"}, False),
    ({"exit_code": 0, "stdout": "scan found 0 failed checks"}, False),
    ({"code": 0}, False),
    ({"exit_code": 0, "stdout": "ok"}, False),
    # explicit failure keys still outrank the zero (U43 semantics kept)
    ({"exit_code": 0, "error": "warning: retry succeeded"}, True),
    ({"exit_code": 0, "status": "error", "output": "ok"}, True),
    # sibling exit keys under a zero primary keep U79 precedence
    ({"exit_code": 0, "code": 500}, True),
    ({"exit_code": 0, "code": 200}, False),
]


@pytest.mark.parametrize("case,expected", _U110_CODE_ZERO_CASES)
def test_u110_zero_exit_defers_to_the_shared_text_scan(case, expected):
    assert looks_like_error(case) is expected


def test_u110_record_level_zero_exit_uses_the_scan():
    record_failure = {
        "text": json.dumps({"code": 0, "stdout": "deploy aborted: payment failed"}),
        "skill": "deploy",
    }
    record_success = {
        "text": json.dumps({"code": 0, "stdout": "nothing failed, 12 passed"}),
        "skill": "deploy",
    }
    assert _is_tool_failure(record_failure, record_failure["text"]) is True
    assert _is_tool_failure(record_success, record_success["text"]) is False
