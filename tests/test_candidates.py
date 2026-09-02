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
