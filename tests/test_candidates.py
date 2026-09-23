import json

import pytest

from hermes_curator_evolver.candidates import (
    CANDIDATE_TYPE_IGNORE,
    CANDIDATE_TYPE_MEMORY,
    CANDIDATE_TYPE_REPLAY_BENCHMARK,
    CANDIDATE_TYPE_SKILL_NEW,
    CANDIDATE_TYPE_SKILL_UPDATE,
    CANDIDATE_TYPES,
    Candidate,
    candidate_id,
    classify_record,
    mine_candidates,
)


def test_candidate_type_constants_match_required_strings():
    assert CANDIDATE_TYPES == {
        "memory",
        "skill_update",
        "skill_new",
        "replay_benchmark",
        "ignore",
    }


def test_candidate_dataclass_defaults_are_safe():
    c = Candidate(
        candidate_type=CANDIDATE_TYPE_MEMORY,
        title="user safety preference",
        rationale="evidence shows preference",
        confidence=0.9,
        evidence_refs=["session:abc"],
    )

    assert c.auto_apply_allowed is False
    assert c.requires_human_review is True
    assert c.metadata == {}
    assert c.target_skill is None
    assert isinstance(c.id, str) and len(c.id) >= 16


def test_candidate_dataclass_refuses_non_human_review_candidates():
    with pytest.raises(ValueError, match="requires_human_review"):
        Candidate(
            candidate_type=CANDIDATE_TYPE_MEMORY,
            title="unsafe",
            rationale="unsafe",
            confidence=0.9,
            evidence_refs=["session:abc"],
            requires_human_review=False,
        )


def test_candidate_id_is_deterministic_and_evidence_order_independent():
    a = candidate_id(CANDIDATE_TYPE_MEMORY, "title", ["a", "b"])
    b = candidate_id(CANDIDATE_TYPE_MEMORY, "title", ["b", "a"])
    c = candidate_id(CANDIDATE_TYPE_MEMORY, "different", ["a", "b"])
    d = candidate_id(CANDIDATE_TYPE_SKILL_NEW, "title", ["a", "b"])

    assert a == b
    assert a != c
    assert a != d


def test_user_preference_safety_text_becomes_memory_candidate():
    text = (
        "curator-evolver may auto-apply only agent-created non-core skills "
        "and must not modify core/official/external skills"
    )

    candidate = classify_record({"text": text, "evidence_ref": "session:abc"})

    assert candidate is not None
    assert candidate.candidate_type == CANDIDATE_TYPE_MEMORY
    assert candidate.confidence >= 0.8
    assert candidate.auto_apply_allowed is False
    assert candidate.requires_human_review is True
    assert "session:abc" in candidate.evidence_refs


def test_chinese_memory_policy_text_becomes_memory_not_ignored():
    text = (
        "durable memory 只存精簡宣告事實；流程/步驟/SOP 進 skill；"
        "不存 task progress / PR / SHA / 短期狀態"
    )

    candidate = classify_record({"text": text, "evidence_ref": "session:memory-policy"})

    assert candidate.candidate_type == CANDIDATE_TYPE_MEMORY
    assert candidate.confidence >= 0.8
    assert candidate.auto_apply_allowed is False
    assert candidate.requires_human_review is True


def test_workflow_text_with_target_skill_becomes_skill_update():
    text = (
        "Workflow to bootstrap curator-evolver: 1. First run "
        "`hermes-curator-evolver backfill-sessions`. "
        "2. Then run `hermes-curator-evolver install-auto --schedule daily`. "
        "3. Finally invoke `hermes-curator-evolver auto-run --apply-low-risk`."
    )

    candidate = classify_record(
        {
            "text": text,
            "evidence_ref": "session:xyz",
            "target_skill": "curator-evolution",
        }
    )

    assert candidate.candidate_type == CANDIDATE_TYPE_SKILL_UPDATE
    assert candidate.target_skill == "curator-evolution"
    assert candidate.auto_apply_allowed is False
    assert candidate.requires_human_review is True


def test_workflow_text_without_target_skill_becomes_skill_new():
    text = (
        "Setup workflow: 1. start the gateway. 2. run `cli ingest`. "
        "3. then verify the output. 4. finally restart."
    )

    candidate = classify_record({"text": text, "evidence_ref": "session:xyz"})

    assert candidate.candidate_type == CANDIDATE_TYPE_SKILL_NEW
    assert candidate.target_skill is None
    assert candidate.auto_apply_allowed is False


def test_chinese_workflow_text_becomes_skill_candidate():
    text = (
        "候選歸納流程：先查 evidence，再產生 redacted trajectory，"
        "最後寫入 review queue；流程/步驟/SOP 進 skill。"
    )

    candidate = classify_record({"text": text, "evidence_ref": "session:zh-workflow"})

    assert candidate.candidate_type == CANDIDATE_TYPE_SKILL_NEW
    assert candidate.confidence >= 0.6


def test_tool_error_event_becomes_replay_benchmark():
    record = {
        "text": "read_file not_found /tmp/missing.md",
        "evidence_ref": "session:err",
        "tool_name": "read_file",
        "is_error": True,
    }

    candidate = classify_record(record)

    assert candidate.candidate_type == CANDIDATE_TYPE_REPLAY_BENCHMARK
    assert candidate.requires_human_review is True
    assert candidate.auto_apply_allowed is False


def test_skill_manage_size_cap_failure_becomes_replay_benchmark():
    record = {
        "text": "skill" + "_" + "manage size cap exceeded: SKILL.md too large",
        "evidence_ref": "session:size",
        "tool_name": "skill" + "_" + "manage",
        "is_error": True,
    }

    candidate = classify_record(record)

    assert candidate.candidate_type == CANDIDATE_TYPE_REPLAY_BENCHMARK


def test_terminal_nonzero_exit_text_becomes_replay_benchmark():
    record = {
        "text": "Traceback: command failed with exit code 2",
        "evidence_ref": "session:term",
        "tool_name": "terminal",
        "is_error": True,
    }

    candidate = classify_record(record)

    assert candidate.candidate_type == CANDIDATE_TYPE_REPLAY_BENCHMARK


def test_ephemeral_pr_progress_text_is_ignored():
    record = {
        "text": "merged PR #1234 at abc1234def into main",
        "evidence_ref": "session:eph",
    }

    candidate = classify_record(record)

    assert candidate.candidate_type == CANDIDATE_TYPE_IGNORE
    assert candidate.auto_apply_allowed is False
    assert candidate.requires_human_review is True


def test_short_issue_number_only_is_ignored():
    record = {"text": "#42", "evidence_ref": "session:short"}

    candidate = classify_record(record)

    assert candidate.candidate_type == CANDIDATE_TYPE_IGNORE


def test_short_sha_only_is_ignored():
    record = {"text": "abc1234def", "evidence_ref": "session:sha"}

    candidate = classify_record(record)

    assert candidate.candidate_type == CANDIDATE_TYPE_IGNORE


def test_near_cap_skill_md_becomes_human_review_with_direct_append_disallowed():
    record = {
        "text": "SKILL.md size is approximately 99500 bytes, near 100k cap",
        "evidence_ref": "session:cap",
        "target_skill": "curator-evolution",
    }

    candidate = classify_record(record)

    assert candidate.candidate_type in {
        CANDIDATE_TYPE_SKILL_UPDATE,
        CANDIDATE_TYPE_REPLAY_BENCHMARK,
    }
    assert candidate.requires_human_review is True
    assert candidate.auto_apply_allowed is False
    assert candidate.metadata.get("direct_append_allowed") is False


def test_over_cap_skill_md_size_field_triggers_human_review_metadata():
    record = {
        "text": "skill is large",
        "evidence_ref": "session:cap2",
        "target_skill": "curator-evolution",
        "skill_md_size": 101000,
    }

    candidate = classify_record(record)

    assert candidate.candidate_type in {
        CANDIDATE_TYPE_SKILL_UPDATE,
        CANDIDATE_TYPE_REPLAY_BENCHMARK,
    }
    assert candidate.requires_human_review is True
    assert candidate.auto_apply_allowed is False
    assert candidate.metadata.get("direct_append_allowed") is False


def test_low_confidence_unknown_text_defaults_to_ignore():
    record = {"text": "qwerty lorem ipsum", "evidence_ref": "session:unknown"}

    candidate = classify_record(record)

    assert candidate.candidate_type == CANDIDATE_TYPE_IGNORE
    assert candidate.auto_apply_allowed is False
    assert candidate.requires_human_review is True


def test_json_wrapped_summary_is_unwrapped_before_classification():
    record = {
        "text": '{"results":[{"summary":"durable memory 只存精簡宣告事實；不存 task progress / PR / SHA / 短期狀態"}]}',
        "evidence_ref": "session:wrapped",
    }

    candidate = classify_record(record)

    assert candidate.candidate_type == CANDIDATE_TYPE_MEMORY
    assert not candidate.rationale.startswith("{")
    assert "durable memory" in candidate.rationale


def test_json_wrapped_workflow_rationale_is_reviewer_readable():
    record = {
        "text": '{"results":[{"summary":"Workflow: 1. First run `ingest`. 2. Then run `mine`. 3. Finally review."}]}',
        "evidence_ref": "session:wrapped-workflow",
    }

    candidate = classify_record(record)

    assert candidate.candidate_type == CANDIDATE_TYPE_SKILL_NEW
    assert not candidate.rationale.startswith("{")
    assert "Workflow:" in candidate.rationale


def test_line_numbered_source_dump_is_ignored_not_workflow():
    record = {
        "text": '{"content":" 1|Workflow to bootstrap: 1. First run `cmd`.\\n 2|Then run `other`.\\n 3|Finally verify."}',
        "evidence_ref": "session:source-dump",
    }

    candidate = classify_record(record)

    assert candidate.candidate_type == CANDIDATE_TYPE_IGNORE


def test_json_exit_code_failure_becomes_replay_without_is_error_flag():
    record = {
        "text": '{"exit_code":1,"output":"command returned stderr but no explicit failed word"}',
        "evidence_ref": "session:json-error",
        "tool_name": "terminal",
    }

    candidate = classify_record(record)

    assert candidate.candidate_type == CANDIDATE_TYPE_REPLAY_BENCHMARK


def test_classify_never_returns_auto_apply_allowed_true():
    records = [
        {"text": "curator-evolver may auto-apply only agent-created non-core skills"},
        {"text": "Workflow: 1. step one 2. step two", "target_skill": "x"},
        {"text": "Traceback: failed", "is_error": True},
        {"text": "merged PR #1"},
        {"text": "qwerty"},
    ]

    for r in records:
        c = classify_record(r)
        assert c.auto_apply_allowed is False


def test_mine_candidates_classifies_each_record():
    records = [
        {"text": "merged PR #1", "evidence_ref": "s:1"},
        {"text": "Traceback: oops", "evidence_ref": "s:2", "is_error": True},
        {
            "text": "curator-evolver may auto-apply only agent-created non-core skills",
            "evidence_ref": "s:3",
        },
    ]

    results = mine_candidates(records)

    assert len(results) == 3
    types = {c.candidate_type for c in results}
    assert {CANDIDATE_TYPE_IGNORE, CANDIDATE_TYPE_REPLAY_BENCHMARK, CANDIDATE_TYPE_MEMORY} <= types


def test_successful_manage_result_with_capability_word_is_not_a_failure():
    # Assessment F2 regression: "cap" substring heuristic read the success
    # message "skill capabilities updated" as a tool failure.
    record = {
        "tool_name": "skill_manage",
        "text": '{"success": true, "message": "skill capabilities updated"}',
        "evidence_ref": "session:cap-false-positive",
    }

    candidate = classify_record(record)

    assert candidate.candidate_type != CANDIDATE_TYPE_REPLAY_BENCHMARK
    assert candidate.metadata.get("is_error") is not True


def test_explicit_success_false_payload_is_classified_as_failure():
    record = {
        "tool_name": "skill_manage",
        "text": '{"success": false}',
        "evidence_ref": "session:structured-failure",
    }

    candidate = classify_record(record)

    assert candidate.candidate_type == CANDIDATE_TYPE_REPLAY_BENCHMARK
    assert candidate.metadata.get("is_error") is True


def test_success_true_payload_beats_error_keyword_scan():
    record = {
        "tool_name": "skill_manage",
        "text": '{"success": true, "exit_code": 0, "message": "scan found 0 failed checks"}',
        "evidence_ref": "session:structured-success-wins",
    }

    candidate = classify_record(record)

    assert candidate.candidate_type != CANDIDATE_TYPE_REPLAY_BENCHMARK
    assert candidate.metadata.get("is_error") is not True


def test_prose_with_two_inline_code_spans_is_not_a_workflow():
    # Assessment F5 regression: two backtick spans in flowing prose used to
    # satisfy the shell_hits >= 2 branch and mint a skill_new candidate.
    record = {
        "tool_name": "bash",
        "text": "I ran `git status` then `git diff` to check.",
        "evidence_ref": "session:inline-prose-not-workflow",
    }

    candidate = classify_record(record)

    assert candidate.candidate_type == CANDIDATE_TYPE_IGNORE


def test_command_sequence_on_own_lines_is_a_workflow():
    record = {
        "tool_name": "bash",
        "text": "Deploy runbook:\n1. `pytest -q`\n2. `curator-evolver apply --approve`\n3. `curator-evolver rollback --manifest m.json`",
        "evidence_ref": "session:block-command-sequence",
    }

    candidate = classify_record(record)

    assert candidate.candidate_type == CANDIDATE_TYPE_SKILL_NEW


def test_looks_like_error_marshals_every_result_shape():
    """U28 / assessment P2: the public classifier is shape-agnostic.

    ``looks_like_error`` accepts the raw tool result in any of the three
    forms callers hand over (str, dict, list) and never crashes on None.
    The structured-failure path comes from the storage ingest side; this
    pins the marshaling contract.
    """

    from hermes_curator_evolver.candidates import looks_like_error

    assert looks_like_error(None) is False
    assert looks_like_error("") is False
    assert looks_like_error("3 passed, no errors found") is False
    assert looks_like_error("Traceback (most recent call last):") is True
    assert looks_like_error({"exit_code": 1, "output": "boom failed"}) is True
    assert looks_like_error({"stdout": "3 passed", "exit_code": 0}) is False
    assert looks_like_error([{"exit_code": 1}]) is True
    assert looks_like_error([{"stdout": "3 passed, no errors found"}]) is False


def test_successful_test_run_summary_is_not_classified_as_error():
    """U28 / assessment P2: a passing pytest summary must not mark an event.

    ``3 passed, no errors found`` carries the word "errors", which the old
    storage-side keyword scan flagged; successful test-run summaries in any
    shape (bare str, JSON payload, stdout field) classify as success.
    """

    from hermes_curator_evolver.candidates import looks_like_error

    assert looks_like_error("3 passed, no errors found") is False
    assert looks_like_error('{"stdout": "3 passed, no errors found", "exit_code": 0}') is False
    assert looks_like_error({"summary": "3 passed, no errors found", "ok": True}) is False
    # while genuine failure markers still fire
    assert looks_like_error("exit code 1: failed") is True
    assert looks_like_error("Traceback ... RuntimeError: exceeded size cap") is True


# ---------------------------------------------------------------------------
# Roadmap U43 (assessment Q1): the classifier truth table. Every probe from
# the adversarial pass-5 corpus is now a permanent regression.
# ---------------------------------------------------------------------------

from hermes_curator_evolver.candidates import looks_like_error


_Q1_CORPUS_SUCCESS = [
    # keyword false positives that must classify as success
    "0 failed, 12 passed",
    "success: no tests failed",
    "grep: 0 failed",
    "exit code 0",
    "exit status 0",
    "3 passed, no errors found",
    # structured success shapes
    {"stdout": "ok", "stderr": ""},
    {"returncode": 0, "stdout": "done"},
    {"code": 0},
    {"ok": True},
    {"success": True},
    {"status": "ok"},
    {"status": "passed", "exit_code": 0},
]

_Q1_CORPUS_FAILURE = [
    # structured failure shapes the old table missed
    {"returncode": 1},
    {"code": 1},
    {"ok": False},
    {"success": False},
    {"status": "error"},
    {"status": "failed"},
    {"exit_code": 1},
    # genuine keyword failures that must still match
    "Traceback (most recent call last)",
    "exit code 1",
    "process exited with status 2",
    "2 failed, 0 passed",
    "grep: pattern not found",
    # exit-status disagreement resolves to failure
    {"ok": True, "exit_code": 1},
    {"exit_code": 0, "error": "boom"},
]


@pytest.mark.parametrize("sample", _Q1_CORPUS_SUCCESS)
def test_u43_success_shapes_are_not_errors(sample):
    assert looks_like_error(sample) is False


@pytest.mark.parametrize("sample", _Q1_CORPUS_FAILURE)
def test_u43_failure_shapes_are_errors(sample):
    assert looks_like_error(sample) is True


def test_u43_zero_exit_status_is_explicit_success_even_with_scary_text():
    payload = {"exit_code": 0, "stderr": "warnings printed, nothing failed"}
    assert looks_like_error(payload) is False


def test_u43_stringified_structured_failure_is_caught():
    text = json.dumps({"returncode": 1, "stderr": "boom"})
    assert looks_like_error(text) is True
    text_ok = json.dumps({"returncode": 0, "stdout": "ok", "stderr": ""})
    assert looks_like_error(text_ok) is False


def test_u43_list_of_results_is_error_iff_any_element_is():
    assert looks_like_error([{"ok": True}, {"code": 1}]) is True
    assert looks_like_error([{"ok": True}, "0 failed, 3 passed"]) is False


# ---------------------------------------------------------------------------
# Roadmap U51 (assessment S1/S2/S4/S7, pass-6 adversarial corpus v2): the
# classifier's second reopen. Every probe below is lifted from
# repro-pass6.py F1/F2/F4/F5 and stays a permanent regression.
# ---------------------------------------------------------------------------

_U51_COUNT_CASES = [
    # S1: the cycle-5 (?<!0\s)failed lookbehind cleared every count ending
    # in a zero — paired counts must bind at ANY digit width.
    ("10 failed, 2 passed in 0.03s", True),
    ("20 failed, 5 errors", True),
    ("100 failed", True),
    ("110 failed", True),
    ("7 failed, 3 passed", True),  # control: non-zero-ending counts always fired
    ("0 failed, 12 passed", False),  # zero-count reports stay success
    ("grep: 0 failed", False),
    ("2 packages failed to install: foo, bar", True),  # keyword without adjacent count
    ("0 failed, 1 failed", True),  # any positive count in the clause wins
]


@pytest.mark.parametrize("payload,expected", _U51_COUNT_CASES)
def test_u51_paired_failure_counts_bind_at_every_digit_width(payload, expected):
    assert looks_like_error(payload) is expected


_U51_CODE_CASES = [
    # S2: tool wrappers store HTTP statuses in the generic ``code`` key
    # verbatim; recognized in-band success statuses are not process
    # failures when no explicit failure field exists.
    ({"code": 200, "status": "OK", "body": "hello"}, False),
    ({"code": 201}, False),
    ({"code": 202, "ok": True}, False),
    ({"code": 204}, False),
    ({"code": 0}, False),
    ({"status_code": 200}, False),  # not an exit-code key at all
    # unrecognized nonzero values keep exit-code semantics
    ({"code": 8080, "listening": True}, True),
    ({"code": 1}, True),
    # explicit failure fields outrank an HTTP-shaped code value
    ({"code": 200, "error": "boom"}, True),
    ({"code": 200, "ok": False}, True),
    ({"code": 200, "status": "error"}, True),
    # unambiguous exit keys keep strict semantics: no HTTP carve-out
    ({"exit_code": 200, "ok": True}, True),
    ({"returncode": 204}, True),
]


@pytest.mark.parametrize("payload,expected", _U51_CODE_CASES)
def test_u51_http_shaped_code_values(payload, expected):
    assert looks_like_error(payload) is expected


_U51_SCOPE_CASES = [
    # S4: a success phrase anywhere in the payload used to clear a real
    # failure; it may only clear the failure keywords in its own clause.
    ("deploy failed: connection refused; earlier healthcheck reported no errors", True),
    ("build exceeded memory limit; cache check: no tests failed", True),
    ("deploy failed: connection refused", True),
    ("deploy failed.\nlater: no errors reported", True),  # different line, same rule
    ("all good: no errors; nothing failed", False),
    ("12 passed, 0 failed", False),
    ("success: no tests failed", False),
]


@pytest.mark.parametrize("payload,expected", _U51_SCOPE_CASES)
def test_u51_success_phrases_clear_only_their_own_clause(payload, expected):
    assert looks_like_error(payload) is expected


def test_u51_zero_exit_truth_matches_the_pinned_code_order():
    # S7: the docstring used to claim "zero → success" while the code checks
    # explicit failure fields FIRST — the behavior is pinned (see
    # ``{"exit_code": 0, "error": "boom"}`` in the U43 corpus above); the
    # U51 docstring now states it. These keep the order pinned so a future
    # reorder fails loudly instead of silently diverging again.
    assert looks_like_error({"exit_code": 0, "error": "warning: retry succeeded"}) is True
    assert looks_like_error({"exit_code": 0, "status": "error", "output": "ok"}) is True
    assert looks_like_error({"returncode": 0, "exception": "handled by caller"}) is True
    assert looks_like_error({"exit_code": 0, "stderr": "warnings printed, nothing failed"}) is False


# ---------------------------------------------------------------------------
# U67 — classifier format-matrix truth (pass-7 N1/N3/N4). The cycle-6 corpus
# pinned digit WIDTHS; it never covered grouping separators ("1,000 failed"
# parsed as 000 → success), unspaced clause joins, or the complete in-band
# HTTP success family. The matrix below crosses widths × separators (`,` `.`
# space `_` — the full L15/KTD31 set, widened by the independent review's
# finding 1) × clause joins, and pins every HTTP code the wrappers emit.
# ---------------------------------------------------------------------------

_U67_WIDTH_SEPARATOR_CASES = [
    # N1: comma-grouped failure counts classify as failure at every
    # magnitude (cycle-6 read "1,000" as 000 → success).
    ("1,000 failed", True),
    ("10,000 failed", True),
    ("1,000,000 failed", True),
    ("2,048 failed", True),  # stay-green control from the batch contract
    ("1,234 failed, 5 passed", True),
    ("Tests: 2,048 failed, 12,030 passed", True),
    # Independent-review finding 1 (L15 separator set): every OTHER
    # grouping separator — not just comma — binds the count at true
    # magnitude. The dot cases also prove the clause splitter no longer
    # breaks "10.000 failed" into "10." + "000 failed" → success.
    ("10.000 failed", True),
    ("1.000.000 failed", True),
    ("10 000 failed", True),
    ("1 234 567 failed", True),
    ("10_000 failed", True),
    ("10,00 failed", True),  # malformed group: failure-shaped text errs loud
    ("12.345 failed, 678 passed", True),
    # Plain widths stay failure (cycle-6 pinned these; matrix re-pins).
    ("1 failed", True),
    ("10 failed", True),
    ("100 failed", True),
    ("10 failed, 2 passed", True),  # stay-green control (assessment S1)
    ("1000000 failed", True),
    # Zero-count claims stay success — and clear the clause only when they
    # are its sole failure evidence (N3).
    ("0 failed, 12 passed", False),  # stay-green control (assessment Q1)
    ("grep: 0 failed", False),
    ("0 failed", False),
    ("0,000 failed, 300 passed", False),
    ("0 failed, deploy failed: connection refused", True),  # N3: claim + failure
    ("0 failed, exit code 1, no errors", False),  # review finding 2: rescan
    ("exit code 1, no errors", False),  # honors the same success-phrase clearing
    ("12 passed, 0 failed", False),
]

_U67_CLAUSE_JOIN_CASES = [
    # N3: the join between a failure and a success phrase must not matter —
    # semicolon, newline, spaced period, and UNSPACED period (models emit
    # concatenated output) all split into separate clauses.
    ("deploy failed; no errors later", True),
    ("deploy failed\nno errors later", True),
    ("deploy failed. no errors later", True),
    ("deploy failed.no errors later", True),  # N3b: unspaced sentence join
    ("deploy failed! no errors later", True),
    ("deploy failed? no errors later", True),
    ("no errors; nothing to report", False),
    ("0 failed.deploy failed: connection refused", True),
    ("10.000 failed.no errors later", True),  # grouping dot ≠ sentence dot
]

_U67_HTTP_CODE_CASES = [
    # N4: the full in-band success family for the generic ``code`` key.
    ({"code": 200}, False),
    ({"code": 201}, False),
    ({"code": 202}, False),
    ({"code": 203}, False),  # cycle-6 miss: 203 is a success
    ({"code": 204}, False),
    ({"code": 206}, False),  # cycle-6 miss: 206 is a success
    ({"code": 301}, False),  # cycle-6 miss: redirects are followed by clients
    ({"code": 302}, False),
    ({"code": 303}, False),
    ({"code": 304}, False),  # conditional-cache success
    ({"code": 307}, False),
    ({"code": 308}, False),
    ({"code": 400}, True),
    ({"code": 401}, True),
    ({"code": 404}, True),
    ({"code": 500}, True),
    ({"code": 502}, True),
    ({"code": 1}, True),
]


@pytest.mark.parametrize("payload,expected", _U67_WIDTH_SEPARATOR_CASES)
def test_u67_grouped_and_plain_failure_counts(payload, expected):
    assert looks_like_error(payload) is expected


@pytest.mark.parametrize("payload,expected", _U67_CLAUSE_JOIN_CASES)
def test_u67_clause_joins_spaced_and_unspaced(payload, expected):
    assert looks_like_error(payload) is expected


@pytest.mark.parametrize("payload,expected", _U67_HTTP_CODE_CASES)
def test_u67_http_success_family_for_generic_code(payload, expected):
    assert looks_like_error(payload) is expected


def test_u67_exit_keys_keep_strict_nonzero_semantics():
    # The widened HTTP family applies ONLY to the ambiguous generic ``code``
    # key; ``exit_code``/``returncode`` stay nonzero-is-failure even at
    # HTTP-looking values (roadmap U51 boundary, re-pinned under U67).
    assert looks_like_error({"exit_code": 301}) is True
    assert looks_like_error({"returncode": 204}) is True
    assert looks_like_error({"exit_code": 0}) is False


_U73_SUCCESS_PHRASE_POSITION_CASES = [
    # F1 (pass-8): a comma-joined success phrase used to clear a LATER
    # genuine failure claim in the same clause. Positional truth (KTD35):
    # the clause's last success phrase answers the evidence that PRECEDES
    # it; a failure keyword after it is a new claim that stands.
    ("no tests failed, deploy failed: connection refused", True),
    ("all tests passed cleanly, but the build failed with exit code 1", True),
    ("no errors, exit code 1", True),  # failure claim AFTER the success phrase
    ("exit code 1, no errors", False),  # review finding 2 stays pinned
    ("0 failed, exit code 1, no errors", False),  # zero count + answered evidence
    ("0 failed, deploy failed: connection refused", True),  # N3 stays pinned
    ("no tests failed", False),
    ("success: no tests failed", False),
    ("grep: 0 failed, 12 passed", False),
]


@pytest.mark.parametrize("payload,expected", _U73_SUCCESS_PHRASE_POSITION_CASES)
def test_u73_success_phrases_answer_only_preceding_evidence(payload, expected):
    assert looks_like_error(payload) is expected


_U73_IN_BAND_RANGE_CASES = [
    # F3 (pass-8): the enumerated in-band set missed legal codes (226 IM
    # Used was the third miss after 203/206); the test is the RANGE.
    ({"code": 226}, False),
    ({"code": 218}, False),  # any 2xx is in-band by construction
    ({"code": 310}, False),  # any 3xx is in-band by construction
    ({"code": 399}, False),
    ({"code": 400}, True),
    ({"code": 418}, True),
    ({"code": 599}, True),
]


@pytest.mark.parametrize("payload,expected", _U73_IN_BAND_RANGE_CASES)
def test_u73_in_band_success_is_a_range_not_a_list(payload, expected):
    assert looks_like_error(payload) is expected


_U73_STATUS_PAYLOAD_CASES = [
    # F4 (pass-8): ``status`` arrives as a bare integer or a status line,
    # not only a vocabulary word; the same 200-399 range governs.
    ({"status": 500}, True),
    ({"status": 504}, True),
    ({"status": 404}, True),
    ({"status": "500 Internal Server Error"}, True),
    ({"status": "403 Forbidden"}, True),
    ({"status": 204}, False),
    ({"status": 302}, False),
    ({"status": "204 No Content"}, False),
    ({"status": "ok"}, False),
    ({"status": "healthy"}, False),
    ({"status": "error"}, True),
    ({"status": "timeout"}, True),
    # explicit failure status outranks a zero exit (U43 order, F4-extended)
    ({"status": 500, "exit_code": 0}, True),
    # in-band status with a plain failing exit stays a failure
    ({"status": 200, "exit_code": 1}, True),
]


@pytest.mark.parametrize("payload,expected", _U73_STATUS_PAYLOAD_CASES)
def test_u73_status_payloads_int_lines_and_words(payload, expected):
    assert looks_like_error(payload) is expected


# ---------------------------------------------------------------------------
# U86 — free-text failure vocabulary widening (cycle 10, pass-7 F4 probes).
# The exit-code arms and the ``failed``-only verb family could not see six
# real-world failure phrasings: the ``ERROR:`` log prefix, bare ``exited 1``
# (no code/status word), the ``failing`` participle, ``N errors`` counts,
# ``timed out``, and ``permission denied``. Each widening is symmetric —
# every success narrative that shares a token with the new arms stays a
# success, answered positionally per KTD35 where applicable.
# ---------------------------------------------------------------------------

_U86_FAILURE_CASES = [
    # pass-7 F4 probe set verbatim
    ("ERROR: file not found", True),
    ("exited 1", True),
    ("3 tests failing", True),
    ("2 errors", True),
    ("timed out", True),
    ("permission denied", True),
    # widened shapes the probes imply
    ("ERRORS: 4 found", True),
    ("process exited 1", True),
    ("exited 2", True),
    ("4 validation errors", True),
    ("1,000 errors", True),
    ("10_000 checks failing", True),
    ("timed_out waiting for lock", True),
    ("Permission Denied", True),
    ({"status": "timed_out"}, True),
    ({"status": "permission_denied"}, True),
]

_U86_SUCCESS_CASES = [
    # zero stays excluded by [1-9]\d* / count>0 at every widening
    ("exited 0", False),
    ("0 errors, 12 passed", False),
    ("0 failing", False),
    ("0 tests failed", False),
    # colon-gated arm: no colon, no keyword hit
    ("error rate healthy", False),
    # no-…-failed family widened in step (success claims answer keywords)
    ("no tests failing", False),
    ("no parse errors", False),
    # bare ``timeout`` stays a status word: config narratives are safe
    ("using a 30s timeout", False),
    # prior truth pins must survive the widening (KTD35 positional rule)
    ("0 failed, exit code 1, no errors", False),
    ("exit code 1, no errors", False),
]


@pytest.mark.parametrize("text,expected", _U86_FAILURE_CASES + _U86_SUCCESS_CASES)
def test_u86_widened_failure_vocabulary(text, expected):
    assert looks_like_error(text) is expected


def test_u86_positional_rule_survives_widened_kinds():
    # The keyword-after-success-claim rule holds for the NEW vocabulary
    # exactly as it does for ``failed``: a failure claim after the last
    # success phrase stands (docstring pin), and a success phrase in a
    # DIFFERENT clause never erases a failing clause (S4).
    assert looks_like_error("no tests failing, deploy timed out: lock held") is True
    assert looks_like_error("no errors\nearlier permission denied on /tmp/x") is True
    # A nonzero count is a standing failure claim even when a success
    # phrase follows in the SAME clause (S1 semantics: "10 failed, 2
    # passed" pins this for ``failed``; the widened kinds inherit it).
    assert looks_like_error("2 errors, no errors since retry") is True
