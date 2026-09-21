"""Pass-7 adversarial probes (read-only against the repo; tmp dirs for state).

In-tree canonical copy (cycle-7 independent-review finding 5): the work-order
citations previously resolved only to the ephemeral /tmp path. REPO is derived
from this file's location so the harness runs from any checkout; run as
`python scripts/repro-pass7.py` and expect `43/43 probes matched sane
expectation` (35 pass-7 + 8 pass-8 records added in cycle 8).
"""
import json
import sys
import time
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from hermes_curator_evolver.candidates import looks_like_error, _text_bears_failure  # noqa: E402
from hermes_curator_evolver.storage import EvidenceStore  # noqa: E402
from hermes_curator_evolver import auto_evolve  # noqa: E402
from hermes_curator_evolver.backfill import _iter_state_sessions, backfill_sessions  # noqa: E402

OUT = []
def rec(name, got, expect, verdict=None):
    ok = verdict if verdict is not None else (got == expect)
    OUT.append((name, got, expect, ok))

print("== K: classifier probes ==")
cases = [
    # (label, input, expected sane answer)
    ("k1a '1,000 failed'", "1,000 failed", True),
    ("k1b '10,000 failed, 3 passed'", "10,000 failed, 3 passed", True),
    ("k1c '2,048 failed' (control)", "2,048 failed", True),
    ("k2 '0 failed, deploy failed: connection refused' (same clause, comma)", "0 failed, deploy failed: connection refused", True),
    ("k2b control: two-line S4 shape", "deploy failed: connection refused\nearlier healthcheck reported no errors", True),
    ("k3a {'code': 203}", {"code": 203}, False),
    ("k3b {'code': 206}", {"code": 206}, False),
    ("k3c {'code': 301}", {"code": 301}, False),
    ("k3d {'code': 304}", {"code": 304}, False),
    ("k4 'deploy failed.no errors later' (no space after period)", "deploy failed.no errors later", True),
    ("stay1 '10 failed, 2 passed'", "10 failed, 2 passed", True),
    ("stay2 '0 failed, 12 passed'", "0 failed, 12 passed", False),
    ("stay3 {'code': 200}", {"code": 200}, False),
    ("stay4 {'returncode': 1}", {"returncode": 1}, True),
    ("stay5 {'ok': False}", {"ok": False}, True),
    ("stay6 {'exit_code': 0, 'error': 'retry succeeded'}", {"exit_code": 0, "error": "retry succeeded"}, True),
]
for label, payload, sane in cases:
    got = looks_like_error(payload)
    rec(label, got, sane)

print("== T1: summary skills DISTINCT event_count vs raw rows ==")
import tempfile
tmp = Path(tempfile.mkdtemp(prefix="pass7-t1-"))
store = EvidenceStore(tmp / "ev.sqlite")
same_second = datetime.now(timezone.utc).isoformat(timespec="seconds")
for _ in range(3):
    store.record_tool_call(
        tool_name="skill_view", args={"name": "demo-skill"},
        result={"ok": True}, task_id="task-1", session_id="sess-1",
        created_at=same_second,
    )
s = store.summary(days=30)
row = (s.get("skills") or [{}])[0]
rec("T1 event_rows", int(row.get("event_rows", -1)), 3)
rec("T1 event_count (distinct)", int(row.get("event_count", -1)), 3)  # sane: 3 attributed actions
rec("T1 summary.skill_events raw", int(s["skill_events"]), 3)
report = {"summary": {"skills": [dict(row)]}}  # fixed cycle-7: _eligible_skill_rows reads ["summary"]["skills"]
elig = auto_evolve._eligible_skill_rows(report, min_evidence=2)
rec("T1b min_evidence=2 gate over 3 same-second events", len(elig), 1)  # sane: eligible

print("== T2: quarantine after connections are cached (mid-process corruption) ==")
tmp2 = Path(tempfile.mkdtemp(prefix="pass7-t2-"))
p = tmp2 / "ev.sqlite"
st = EvidenceStore(p)
st.record_tool_call(tool_name="read_file", args={"path": "x"}, result="ok",
                    task_id="t", session_id="s")
_ = st.summary(days=30)  # cache the read connection too
# Simulate in-place corruption (truncation / garbage overwrite):
p.write_bytes(b"NOT A DATABASE" * 64)
try:
    st2 = EvidenceStore(p)  # __init__ -> init_db on the SAME process (cached writer conn)
    outcome = "recovered"
    st2.record_tool_call(tool_name="read_file", args={"path": "y"}, result="ok",
                         task_id="t2", session_id="s2")
    s2 = st2.summary(days=30)
    outcome = f"recovered, tool_events={s2['tool_events']}"
except Exception as exc:
    outcome = f"{type(exc).__name__}: {exc}"
corrupt_files = sorted(x.name for x in tmp2.iterdir())
rec("T2 EvidenceStore() after in-place corruption", outcome, "recovered",
    verdict=outcome.startswith("recovered"))
OUT.append(("T2 dir contents", corrupt_files, "-", True))

print("== B: backfill probes ==")
now = datetime.now(timezone.utc)

def mkdb(sessions, *, hostile_mint=False, page_size=200):
    class FakeDB:
        def __init__(self):
            self.calls = 0
            self._minted = 0
        def search_sessions(self, source=None, limit=20, offset=0):
            self.calls += 1
            if hostile_mint:
                base = self._minted
                self._minted += page_size
                return [
                    {"id": f"mint-{base + i}", "last_active": now.timestamp() - i,
                     "started_at": now.timestamp() - i, "model": "m", "source": "desktop"}
                    for i in range(page_size)
                ]
            if offset >= len(sessions):
                return []
            return sessions[offset:offset + limit]
        def get_messages(self, session_id, *, include_compacted=False):
            return [{"role": "user", "content": f"use the {session_id} skill"}]
    return FakeDB()

def mk(n, *, old=0):
    rows = []
    for i in range(n):
        age_days = 0.01 * (n - i)
        if i >= n - old:
            age_days = 40
        rows.append({"id": f"s{i:05d}", "last_active": (now - timedelta(days=age_days)).timestamp(),
                     "started_at": (now - timedelta(days=age_days)).timestamp(),
                     "model": "m", "source": "desktop"})
    return rows

# B1: truthful counters + newest-first on an honest 5-session store, limit 2
stats = {}
got_ids = [d["id"] for d in _iter_state_sessions(mkdb(mk(5)), 2, now - timedelta(days=30), stats)]
rec("B1 newest-2 selected", got_ids, ["s00004", "s00003"])
rec("B1 sessions_seen(=metadata_seen)", stats.get("sessions_seen"), 5)
rec("B1 in_window", stats.get("sessions_in_window"), 5)
rec("B1 selected", stats.get("sessions_selected"), 2)
rec("B1 pages_scanned", stats.get("sessions_pages_scanned"), 1)

# B1b: old sessions counted as skipped_old, not seen-as-new
stats_b = {}
got_ids_b = [d["id"] for d in _iter_state_sessions(mkdb(mk(4, old=1)), 10, now - timedelta(days=30), stats_b)]
rec("B1b old session excluded", got_ids_b, ["s00002", "s00001", "s00000"])  # fixed cycle-7: s00003 is the old session, correctly excluded
rec("B1b skipped_old", stats_b.get("sessions_skipped_old"), 1)

# B2: hostile always-minting pagination — runaway bound + disclosure
stats_c = {}
t0 = time.time()
n_yielded = 0
for _d in _iter_state_sessions(mkdb(None, hostile_mint=True), 5, now - timedelta(days=30), stats_c):
    n_yielded += 1
elapsed = time.time() - t0
rec("B2 hostile mint: truncation disclosed", stats_c.get("metadata_scan_truncated"), 1)
OUT.append((f"B2 hostile mint: distinct seen={stats_c.get('sessions_metadata_seen')} "
            f"yielded={n_yielded} elapsed={elapsed:.2f}s", "-", "-", True))

# B3: 12k-session honest store, limit 2 — S3 regression check
rows12k = mk(12_000)
stats_d = {}
t0 = time.time()
got12 = [d["id"] for d in _iter_state_sessions(mkdb(rows12k), 2, now - timedelta(days=30), stats_d)]
elapsed = time.time() - t0
rec("B3 12k store newest-2", got12, ["s11999", "s11998"])
OUT.append((f"B3 12k scan: pages={stats_d.get('sessions_pages_scanned')} "
            f"seen={stats_d.get('sessions_metadata_seen')} elapsed={elapsed:.2f}s", "-", "-", True))

print("== S6/P1 stay-set checks ==")
from hermes_curator_evolver.storage import _extract_skill_name
rec("S6 skill_view({'skills': ['demo']})", _extract_skill_name("skill_view", {"skills": ["demo"]}), "demo")
blocky = "x\n<!-- curator-evolver:auto:start -->\nold \\1 \\g<boom> content\n<!-- curator-evolver:auto:end -->\ny"
try:
    new = auto_evolve._apply_managed_block(blocky, "NEW \\1 BLOCK")
    rec("P1 replacement-injection stays fixed", "NEW \\1 BLOCK" in new and "old" not in new, True)
except Exception as exc:
    rec("P1 replacement-injection stays fixed", f"{type(exc).__name__}: {exc}", True)

print("== P8: pass-8 adversarial probes (cycle-8 U73/U74/U76) ==")
p8_cases = [
    # F1: comma-joined success phrase must not clear a LATER failure claim.
    ("f1a 'no tests failed, deploy failed: connection refused'", "no tests failed, deploy failed: connection refused", True),
    ("f1b 'all tests passed cleanly, but the build failed with exit code 1'", "all tests passed cleanly, but the build failed with exit code 1", True),
    # F3: in-band test is the range, not the enumerated set (226 IM Used).
    ("f3 {'code': 226}", {"code": 226}, False),
    # F4: integer and status-line payloads carry the range rule.
    ("f4a {'status': 500}", {"status": 500}, True),
    ("f4b {'status': '500 Internal Server Error'}", {"status": "500 Internal Server Error"}, True),
]
for label, payload, sane in p8_cases:
    rec(label, looks_like_error(payload), sane)

# F2: two id-less calls to the same tool in DIFFERENT messages of one
# session must import as two events (session-unique fallback id).
import tempfile as _tf
_p8 = Path(_tf.mkdtemp(prefix="pass8-f2-"))
_legacy = _p8 / "legacy"
_legacy.mkdir()
(_legacy / "session_p8.json").write_text(
    json.dumps(
        {
            "session_id": "p8",
            "started_at": datetime.now(UTC).isoformat(),
            "last_active": datetime.now(UTC).isoformat(),
            "messages": [
                {"role": "assistant", "tool_calls": [{"function": {"name": "web_search", "arguments": "{\"q\": \"a\"}"}}]},
                {"role": "assistant", "tool_calls": [{"function": {"name": "web_search", "arguments": "{\"q\": \"b\"}"}}]},
            ],
        }
    ),
    encoding="utf-8",
)
_store8 = EvidenceStore(_p8 / "ev.sqlite")
_r8 = backfill_sessions(sessions_dir=_legacy, store=_store8, days=365)
rec("f2 two id-less same-tool calls in different messages import as 2 events", _r8["tool_events_imported"], 2)
_r8b = backfill_sessions(sessions_dir=_legacy, store=_store8, days=365)
rec("f2 re-import stays idempotent with disclosed skips", (_r8b["tool_events_imported"], _r8b["tool_events_skipped_duplicate"]), (0, 2))
_store8.close()

# P8 (carried): an undecodable legacy file is counted and skipped, never
# aborting the import.
_p8b = Path(_tf.mkdtemp(prefix="pass8-p8-"))
_legacy2 = _p8b / "legacy"
_legacy2.mkdir()
(_legacy2 / "session_bad.json").write_bytes(b"{\"session_id\": \"bad\", \"\xff\": \"\xfe\"}")
_store9 = EvidenceStore(_p8b / "ev.sqlite")
_r9 = backfill_sessions(sessions_dir=_legacy2, store=_store9, days=365)
rec("p8 undecodable legacy file counted and skipped", (_r9["legacy_skipped_undecodable"], _r9["files_failed"]), (1, 0))
_store9.close()

print()
fails = 0
for name, got, expect, ok in OUT:
    mark = "OK " if ok else "FAIL"
    if not ok:
        fails += 1
    print(f"[{mark}] {name}: got={got!r} expect={expect!r}")
print(f"\n{len(OUT) - fails}/{len(OUT)} probes matched the sane expectation; {fails} DEVIATIONS")
