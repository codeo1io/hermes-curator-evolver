import json
from pathlib import Path

import hermes_curator_evolver.auto_evolve as auto_evolve
from hermes_curator_evolver.auto_evolve import (
    AutoEvolveConfig,
    build_low_risk_skill_update,
    discover_channel_bound_skills,
    discover_skill_files,
    generate_variants,
    install_auto_timer,
    run_auto_evolve,
    select_winning_variant,
    uninstall_auto_timer,
)
from hermes_curator_evolver.guarded_apply import sha256_file
from hermes_curator_evolver.storage import EvidenceStore


def _write_skill(root: Path, name: str, body: str = "Use this skill for gateway troubleshooting.") -> Path:
    path = root / name / "SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        f"---\nname: {name}\ndescription: test skill\n---\n\n# {name}\n\n{body}\n",
        encoding="utf-8",
    )
    return path


def test_discover_skill_files_uses_frontmatter_name(tmp_path):
    skills = tmp_path / "skills"
    skill_file = _write_skill(skills, "hermes-agent")

    discovered = discover_skill_files(skills)

    assert discovered["hermes-agent"] == skill_file


def test_discover_channel_bound_skills_reads_hermes_config_aliases(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text(
        """
slack:
  channel_skill_bindings:
    - id: C123
      skills:
        - angi-edge-store-operations
        - service/business-zero-ai-event-triage
""".strip(),
        encoding="utf-8",
    )

    discovered = discover_channel_bound_skills(config)

    assert "angi-edge-store-operations" in discovered
    assert "service/business-zero-ai-event-triage" in discovered
    assert "business-zero-ai-event-triage" in discovered


def test_auto_evolve_default_paths_follow_active_hermes_home(tmp_path, monkeypatch):
    hermes_home = tmp_path / "AppData" / "Local" / "hermes"
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))

    assert auto_evolve._default_skills_dir() == hermes_home / "skills"
    assert auto_evolve._default_hermes_config_path() == hermes_home / "config.yaml"
    assert auto_evolve._default_backup_dir() == hermes_home / "plugins" / "curator-evolver" / "backups"


def test_auto_evolve_protects_channel_bound_skills_from_auto_apply(tmp_path):
    db = tmp_path / "evidence.sqlite"
    store = EvidenceStore(db)
    skills = tmp_path / "skills"
    backups = tmp_path / "backups"
    config = tmp_path / "config.yaml"
    skill_file = _write_skill(skills, "store-playbook")
    original_hash = sha256_file(skill_file)
    config.write_text(
        """
slack:
  channel_skill_bindings:
    - id: C123
      skills:
        - store-playbook
""".strip(),
        encoding="utf-8",
    )
    store.record_tool_call(
        tool_name="skill_view",
        args={"name": "store-playbook"},
        result={"success": True},
        session_id="s1",
    )

    result = run_auto_evolve(
        AutoEvolveConfig(
            db_path=db,
            skills_dir=skills,
            backup_dir=backups,
            hermes_config_path=config,
            days=30,
            min_evidence=1,
            apply_low_risk=True,
            approve_auto_apply=True,
        )
    )

    candidate = result["candidates"][0]
    assert result["summary"]["applied"] == 0
    assert candidate["channel_bound"] is True
    assert candidate["status"] == "skipped"
    assert candidate["reason"] == "channel-bound-skill-auto-apply-protected"
    assert sha256_file(skill_file) == original_hash


def test_auto_evolve_enforces_size_budget_even_when_channel_bound_skill_is_allowlisted(tmp_path):
    db = tmp_path / "evidence.sqlite"
    store = EvidenceStore(db)
    skills = tmp_path / "skills"
    backups = tmp_path / "backups"
    config = tmp_path / "config.yaml"
    skill_file = _write_skill(skills, "store-playbook", "A" * 12_500)
    original_hash = sha256_file(skill_file)
    config.write_text(
        """
slack:
  channel_skill_bindings:
    - id: C123
      skills:
        - store-playbook
""".strip(),
        encoding="utf-8",
    )
    store.record_tool_call(
        tool_name="skill_view",
        args={"name": "store-playbook"},
        result={"success": True},
        session_id="s1",
    )

    result = run_auto_evolve(
        AutoEvolveConfig(
            db_path=db,
            skills_dir=skills,
            backup_dir=backups,
            hermes_config_path=config,
            days=30,
            min_evidence=1,
            apply_low_risk=True,
            approve_auto_apply=True,
            auto_apply_allowlist=("store-playbook",),
        )
    )

    candidate = result["candidates"][0]
    assert result["summary"]["applied"] == 0
    assert candidate["reason"] == "channel-bound-skill-over-size-budget"
    assert candidate["content_size"]["current_chars"] > candidate["content_size"]["auto_loaded_skill_max_chars"]
    assert sha256_file(skill_file) == original_hash


def test_low_risk_update_preserves_existing_skill_and_appends_managed_block(tmp_path):
    skill_file = _write_skill(tmp_path, "hermes-agent")
    original = skill_file.read_text(encoding="utf-8")
    evidence = [
        {
            "created_at": "2026-05-03T10:00:00+00:00",
            "tool_name": "terminal",
            "is_error": True,
            "result_preview": "exit_code 1: gateway restart failed",
        }
    ]

    updated = build_low_risk_skill_update(
        skill_name="hermes-agent",
        skill_text=original,
        days=7,
        summary={"tool_events": 3, "skill_events": 2, "error_events": 1},
        evidence_rows=evidence,
    )

    assert updated.startswith(original)
    assert "<!-- curator-evolver:auto:start -->" in updated
    assert "gateway restart failed" in updated
    assert "Low-risk bounded auto-curation" in updated


def test_auto_evolve_dry_run_plans_low_risk_updates_without_writing(tmp_path):
    db = tmp_path / "evidence.sqlite"
    store = EvidenceStore(db)
    skills = tmp_path / "skills"
    skill_file = _write_skill(skills, "hermes-agent")
    original_hash = sha256_file(skill_file)
    store.record_tool_call(
        tool_name="skill_view",
        args={"name": "hermes-agent"},
        result={"success": True},
        session_id="s1",
    )
    store.record_tool_call(
        tool_name="terminal",
        args={"skills": ["hermes-agent"]},
        result={"exit_code": 1, "output": "restart failed"},
        session_id="s1",
    )

    result = run_auto_evolve(
        AutoEvolveConfig(
            db_path=db,
            skills_dir=skills,
            days=30,
            min_evidence=1,
            apply_low_risk=False,
            approve_auto_apply=False,
        )
    )

    assert result["mode"] == "dry-run"
    assert result["summary"]["planned"] == 1
    assert result["summary"]["applied"] == 0
    assert result["candidates"][0]["skill_name"] == "hermes-agent"
    assert result["candidates"][0]["risk"] == "low"
    assert sha256_file(skill_file) == original_hash


def test_auto_evolve_apply_low_risk_updates_skill_with_backup(tmp_path):
    db = tmp_path / "evidence.sqlite"
    store = EvidenceStore(db)
    skills = tmp_path / "skills"
    backups = tmp_path / "backups"
    skill_file = _write_skill(skills, "store-playbook")
    store.record_tool_call(
        tool_name="skill_view",
        args={"name": "store-playbook"},
        result={"success": True},
        session_id="s1",
    )

    result = run_auto_evolve(
        AutoEvolveConfig(
            db_path=db,
            skills_dir=skills,
            backup_dir=backups,
            days=30,
            min_evidence=1,
            apply_low_risk=True,
            approve_auto_apply=True,
        )
    )

    updated = skill_file.read_text(encoding="utf-8")
    assert result["mode"] == "apply-low-risk"
    assert result["summary"]["applied"] == 1
    assert result["candidates"][0]["apply_result"]["applied"] is True
    assert "Auto-curated evidence notes" in updated
    assert Path(result["candidates"][0]["apply_result"]["manifest_path"]).exists()


def test_auto_evolve_spills_near_limit_evidence_to_reference_file(tmp_path):
    db = tmp_path / "evidence.sqlite"
    store = EvidenceStore(db, preview_chars=6_000)
    skills = tmp_path / "skills"
    backups = tmp_path / "backups"
    base_body = "A" * 98_600
    skill_file = _write_skill(skills, "store-playbook", base_body)
    long_preview = "overflow evidence " + "B" * 4_000
    store.record_tool_call(
        tool_name="terminal",
        args={"skills": ["store-playbook"]},
        result={"exit_code": 1, "output": long_preview},
        session_id="s1",
    )

    result = run_auto_evolve(
        AutoEvolveConfig(
            db_path=db,
            skills_dir=skills,
            backup_dir=backups,
            days=30,
            min_evidence=1,
            apply_low_risk=True,
            approve_auto_apply=True,
        )
    )

    candidate = result["candidates"][0]
    updated = skill_file.read_text(encoding="utf-8")
    references = sorted((skill_file.parent / "references").glob("curator-evolver-auto-*.md"))
    assert result["summary"]["applied"] == 1
    assert candidate["size_strategy"] == "reference-spillover"
    assert len(updated) <= 100_000
    assert "Detailed evidence moved to" in updated
    assert long_preview not in updated
    assert references, "expected detailed evidence spillover reference file"
    assert long_preview in references[0].read_text(encoding="utf-8")


def test_auto_evolve_skips_apply_when_skill_already_exceeds_hard_cap(tmp_path):
    db = tmp_path / "evidence.sqlite"
    store = EvidenceStore(db)
    skills = tmp_path / "skills"
    backups = tmp_path / "backups"
    skill_file = _write_skill(skills, "store-playbook", "A" * 100_200)
    original_hash = sha256_file(skill_file)
    store.record_tool_call(
        tool_name="skill_view",
        args={"name": "store-playbook"},
        result={"success": True},
        session_id="s1",
    )

    result = run_auto_evolve(
        AutoEvolveConfig(
            db_path=db,
            skills_dir=skills,
            backup_dir=backups,
            days=30,
            min_evidence=1,
            apply_low_risk=True,
            approve_auto_apply=True,
        )
    )

    candidate = result["candidates"][0]
    assert result["summary"]["applied"] == 0
    assert candidate["status"] == "skipped"
    assert candidate["reason"] == "skill-content-hard-cap"
    assert sha256_file(skill_file) == original_hash


def test_auto_evolve_refuses_apply_without_auto_approval(tmp_path):
    db = tmp_path / "evidence.sqlite"
    store = EvidenceStore(db)
    skills = tmp_path / "skills"
    skill_file = _write_skill(skills, "hermes-agent")
    original_hash = sha256_file(skill_file)
    store.record_tool_call(
        tool_name="skill_view",
        args={"name": "hermes-agent"},
        result={"success": True},
        session_id="s1",
    )

    result = run_auto_evolve(
        AutoEvolveConfig(
            db_path=db,
            skills_dir=skills,
            days=30,
            min_evidence=1,
            apply_low_risk=True,
            approve_auto_apply=False,
        )
    )

    assert result["summary"]["applied"] == 0
    assert result["candidates"][0]["apply_result"]["reason"] == "auto-approval-required"
    assert sha256_file(skill_file) == original_hash


def test_auto_evolve_skips_pinned_skills_even_with_auto_approval(tmp_path):
    db = tmp_path / "evidence.sqlite"
    store = EvidenceStore(db)
    skills = tmp_path / "skills"
    skill_file = _write_skill(skills, "hermes-agent")
    text = skill_file.read_text(encoding="utf-8")
    skill_file.write_text(text.replace("description: test skill", "description: test skill\npin: true"), encoding="utf-8")
    original_hash = sha256_file(skill_file)
    store.record_tool_call(
        tool_name="skill_view",
        args={"name": "hermes-agent"},
        result={"success": True},
        session_id="s1",
    )

    result = run_auto_evolve(
        AutoEvolveConfig(
            db_path=db,
            skills_dir=skills,
            days=30,
            min_evidence=1,
            apply_low_risk=True,
            approve_auto_apply=True,
        )
    )

    assert result["summary"]["applied"] == 0
    assert result["summary"]["skipped"] == 1
    assert result["candidates"][0]["reason"] == "pinned-skill"
    assert sha256_file(skill_file) == original_hash


class FakeEmbeddingBackend:
    def encode(self, texts, **kwargs):
        vectors = []
        for text in texts:
            lowered = text.lower()
            if "gateway" in lowered or "restart" in lowered:
                vectors.append([1.0, 0.0])
            elif "music" in lowered:
                vectors.append([0.0, 1.0])
            else:
                vectors.append([0.2, 0.2])
        return vectors


class FakeRerankerBackend:
    def predict(self, pairs):
        return [10.0 if "plugin" in text.lower() else 1.0 for _query, text in pairs]


def test_auto_evolve_semantic_rerank_reorders_evidence_eligible_skills(tmp_path):
    db = tmp_path / "evidence.sqlite"
    store = EvidenceStore(db)
    skills = tmp_path / "skills"
    _write_skill(skills, "plain-gateway", "Troubleshoot gateway restart.")
    _write_skill(skills, "plugin-gateway", "Troubleshoot gateway restart and plugin CLI wiring.")
    store.record_tool_call(
        tool_name="terminal",
        args={"skills": ["plain-gateway"]},
        result={"exit_code": 1, "output": "gateway restart failed"},
        session_id="s1",
    )
    store.record_tool_call(
        tool_name="terminal",
        args={"skills": ["plugin-gateway"]},
        result={"exit_code": 1, "output": "gateway plugin restart failed"},
        session_id="s2",
    )

    result = run_auto_evolve(
        AutoEvolveConfig(
            db_path=db,
            skills_dir=skills,
            days=30,
            min_evidence=1,
            max_skills=2,
            semantic_candidates=True,
            rerank_candidates=True,
            embedding_backend=FakeEmbeddingBackend(),
            reranker_backend=FakeRerankerBackend(),
        )
    )

    assert result["selection"]["mode"] == "semantic-reranked"
    assert result["selection"]["models"]["embedding"] == "Qwen3-Embedding-0.6B"
    assert result["selection"]["models"]["reranker"] == "bge-reranker-v2-m3"
    assert result["candidates"][0]["skill_name"] == "plugin-gateway"
    assert result["candidates"][0]["selection"]["score"] == 10.0
    assert "reranker relevance score" in result["candidates"][0]["selection"]["reasons"]


def test_auto_evolve_semantic_does_not_select_skills_without_evidence_threshold(tmp_path):
    db = tmp_path / "evidence.sqlite"
    store = EvidenceStore(db)
    skills = tmp_path / "skills"
    _write_skill(skills, "plain-gateway", "Troubleshoot gateway restart.")
    _write_skill(skills, "plugin-gateway", "Troubleshoot gateway restart and plugin CLI wiring.")
    store.record_tool_call(
        tool_name="terminal",
        args={"skills": ["plain-gateway"]},
        result={"exit_code": 1, "output": "gateway restart failed"},
        session_id="s1",
    )

    result = run_auto_evolve(
        AutoEvolveConfig(
            db_path=db,
            skills_dir=skills,
            days=30,
            min_evidence=1,
            max_skills=2,
            semantic_candidates=True,
            embedding_backend=FakeEmbeddingBackend(),
        )
    )

    assert [candidate["skill_name"] for candidate in result["candidates"]] == ["plain-gateway"]
    assert result["selection"]["eligible_skill_count"] == 1


def test_install_auto_timer_can_opt_into_semantic_and_rerank_candidates(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))

    result = install_auto_timer(
        schedule="daily",
        skills_dir=tmp_path / "skills",
        enable=False,
        rerank_candidates=True,
    )

    command = result["command"]
    timer_text = Path(result["timer_path"]).read_text(encoding="utf-8")
    service_text = Path(result["service_path"]).read_text(encoding="utf-8")
    assert "--semantic-candidates" in command
    assert "--rerank-candidates" in command
    assert "--semantic-candidates" in service_text
    assert "OnCalendar=daily" in timer_text


def test_install_auto_timer_uses_launchd_on_macos(tmp_path, monkeypatch):
    monkeypatch.setattr(auto_evolve.sys, "platform", "darwin")
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes-profile"))

    result = install_auto_timer(
        schedule="daily",
        skills_dir=tmp_path / "skills",
        enable=False,
        rerank_candidates=True,
    )

    plist_path = Path(result["plist_path"])
    plist_text = plist_path.read_text(encoding="utf-8")
    assert result["scheduler"] == "launchd"
    assert plist_path == tmp_path / "home" / "Library" / "LaunchAgents" / "com.pingchesu.hermes-curator-evolver.auto.plist"
    assert result["service_path"] is None
    assert result["timer_path"] is None
    assert "<key>ProgramArguments</key>" in plist_text
    assert "<string>--semantic-candidates</string>" in plist_text
    assert "<string>--rerank-candidates</string>" in plist_text
    assert "<key>StartCalendarInterval</key>" in plist_text
    assert "<key>Hour</key>" in plist_text
    assert str(tmp_path / "hermes-profile" / "plugins" / "curator-evolver" / "logs") in plist_text


def test_install_auto_timer_launchd_hourly_uses_start_interval(tmp_path, monkeypatch):
    monkeypatch.setattr(auto_evolve.sys, "platform", "darwin")
    monkeypatch.setenv("HOME", str(tmp_path / "home"))

    result = install_auto_timer(
        schedule="hourly",
        skills_dir=tmp_path / "skills",
        apply_low_risk=False,
        enable=False,
    )

    plist_text = Path(result["plist_path"]).read_text(encoding="utf-8")
    assert result["schedule"] == "hourly"
    assert result["auto_apply_policy"] == "dry-run-only"
    assert "<key>StartInterval</key>" in plist_text
    assert "<integer>3600</integer>" in plist_text
    assert "--apply-low-risk" not in result["command"]


def test_uninstall_auto_timer_removes_launchd_plist_on_macos(tmp_path, monkeypatch):
    monkeypatch.setattr(auto_evolve.sys, "platform", "darwin")
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    installed = install_auto_timer(schedule="daily", skills_dir=tmp_path / "skills", enable=False)

    result = uninstall_auto_timer(disable=False)

    assert installed["plist_path"] in result["removed"]
    assert not Path(installed["plist_path"]).exists()


def test_auto_evolve_auto_apply_skips_core_skills_by_default_but_applies_non_core(tmp_path):
    db = tmp_path / "evidence.sqlite"
    store = EvidenceStore(db)
    skills = tmp_path / "skills"
    backups = tmp_path / "backups"
    core_file = _write_skill(skills, "hermes-agent", "Hermes runtime and skill loading operations.")
    non_core_file = _write_skill(skills, "store-playbook", "Store operations playbook.")
    core_hash = sha256_file(core_file)

    for skill in ("hermes-agent", "store-playbook"):
        store.record_tool_call(
            tool_name="skill_view",
            args={"name": skill},
            result={"success": True},
            session_id=f"s-{skill}",
        )

    result = run_auto_evolve(
        AutoEvolveConfig(
            db_path=db,
            skills_dir=skills,
            backup_dir=backups,
            days=30,
            min_evidence=1,
            max_skills=5,
            apply_low_risk=True,
            approve_auto_apply=True,
        )
    )

    by_name = {candidate["skill_name"]: candidate for candidate in result["candidates"]}
    assert result["safety"]["protect_core_skills"] is True
    assert result["safety"]["auto_apply_policy"] == "local-agent-created-skills-only"
    assert by_name["hermes-agent"]["status"] == "skipped"
    assert by_name["hermes-agent"]["reason"] == "core-skill-auto-apply-protected"
    assert "apply_result" not in by_name["hermes-agent"]
    assert by_name["store-playbook"]["status"] == "applied"
    assert by_name["store-playbook"]["apply_result"]["applied"] is True
    assert result["summary"]["applied"] == 1
    assert sha256_file(core_file) == core_hash
    assert "Auto-curated evidence notes" in non_core_file.read_text(encoding="utf-8")


def test_auto_evolve_dry_run_still_plans_core_skills_for_review(tmp_path):
    db = tmp_path / "evidence.sqlite"
    store = EvidenceStore(db)
    skills = tmp_path / "skills"
    skill_file = _write_skill(skills, "hermes-agent")
    original_hash = sha256_file(skill_file)
    store.record_tool_call(
        tool_name="skill_view",
        args={"name": "hermes-agent"},
        result={"success": True},
        session_id="s1",
    )

    result = run_auto_evolve(
        AutoEvolveConfig(
            db_path=db,
            skills_dir=skills,
            days=30,
            min_evidence=1,
            apply_low_risk=False,
        )
    )

    assert result["mode"] == "dry-run"
    assert result["candidates"][0]["skill_name"] == "hermes-agent"
    assert result["candidates"][0]["status"] == "planned"
    assert result["summary"]["planned"] == 1
    assert sha256_file(skill_file) == original_hash


def test_auto_evolve_allowlist_can_explicitly_permit_one_core_skill(tmp_path):
    db = tmp_path / "evidence.sqlite"
    store = EvidenceStore(db)
    skills = tmp_path / "skills"
    backups = tmp_path / "backups"
    skill_file = _write_skill(skills, "hermes-agent")
    store.record_tool_call(
        tool_name="skill_view",
        args={"name": "hermes-agent"},
        result={"success": True},
        session_id="s1",
    )

    result = run_auto_evolve(
        AutoEvolveConfig(
            db_path=db,
            skills_dir=skills,
            backup_dir=backups,
            days=30,
            min_evidence=1,
            apply_low_risk=True,
            approve_auto_apply=True,
            auto_apply_allowlist=("hermes-agent",),
        )
    )

    assert result["summary"]["applied"] == 1
    assert result["candidates"][0]["status"] == "applied"
    assert result["candidates"][0]["apply_result"]["applied"] is True
    assert "Auto-curated evidence notes" in skill_file.read_text(encoding="utf-8")


def test_auto_evolve_skips_bundled_manifest_skill_even_if_allowlisted(tmp_path):
    db = tmp_path / "evidence.sqlite"
    store = EvidenceStore(db)
    hermes_home = tmp_path / ".hermes"
    skills = hermes_home / "skills"
    backups = tmp_path / "backups"
    skill_file = _write_skill(skills, "spotify", "Official music skill.")
    (skills / ".bundled_manifest").write_text("spotify:abc123\n", encoding="utf-8")
    original_hash = sha256_file(skill_file)
    store.record_tool_call(
        tool_name="skill_view",
        args={"name": "spotify"},
        result={"success": True},
        session_id="s1",
    )

    result = run_auto_evolve(
        AutoEvolveConfig(
            db_path=db,
            skills_dir=skills,
            backup_dir=backups,
            days=30,
            min_evidence=1,
            apply_low_risk=True,
            approve_auto_apply=True,
            auto_apply_allowlist=("spotify",),
        )
    )

    candidate = result["candidates"][0]
    assert candidate["source"] == "bundled"
    assert candidate["status"] == "skipped"
    assert candidate["reason"] == "source-not-agent-created"
    assert "apply_result" not in candidate
    assert result["summary"]["applied"] == 0
    assert sha256_file(skill_file) == original_hash


def test_auto_evolve_skips_hub_installed_skill(tmp_path):
    db = tmp_path / "evidence.sqlite"
    store = EvidenceStore(db)
    hermes_home = tmp_path / ".hermes"
    skills = hermes_home / "skills"
    backups = tmp_path / "backups"
    skill_file = _write_skill(skills, "community-skill", "Hub installed skill.")
    hub_dir = skills / ".hub"
    hub_dir.mkdir(parents=True)
    (hub_dir / "lock.json").write_text(
        json.dumps({"version": 1, "installed": {"community-skill": {"source": "github"}}}),
        encoding="utf-8",
    )
    original_hash = sha256_file(skill_file)
    store.record_tool_call(
        tool_name="skill_view",
        args={"name": "community-skill"},
        result={"success": True},
        session_id="s1",
    )

    result = run_auto_evolve(
        AutoEvolveConfig(
            db_path=db,
            skills_dir=skills,
            backup_dir=backups,
            days=30,
            min_evidence=1,
            apply_low_risk=True,
            approve_auto_apply=True,
        )
    )

    candidate = result["candidates"][0]
    assert candidate["source"] == "hub-installed"
    assert candidate["status"] == "skipped"
    assert candidate["reason"] == "source-not-agent-created"
    assert result["summary"]["applied"] == 0
    assert sha256_file(skill_file) == original_hash


def test_auto_evolve_skips_external_dir_skill(tmp_path, monkeypatch):
    db = tmp_path / "evidence.sqlite"
    store = EvidenceStore(db)
    hermes_home = tmp_path / ".hermes"
    hermes_home.mkdir()
    external = tmp_path / "team-skills"
    backups = tmp_path / "backups"
    skill_file = _write_skill(external, "team-playbook", "Shared team skill.")
    (hermes_home / "config.yaml").write_text(
        f"skills:\n  external_dirs:\n    - {external}\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))
    original_hash = sha256_file(skill_file)
    store.record_tool_call(
        tool_name="skill_view",
        args={"name": "team-playbook"},
        result={"success": True},
        session_id="s1",
    )

    result = run_auto_evolve(
        AutoEvolveConfig(
            db_path=db,
            skills_dir=external,
            backup_dir=backups,
            days=30,
            min_evidence=1,
            apply_low_risk=True,
            approve_auto_apply=True,
        )
    )

    candidate = result["candidates"][0]
    assert candidate["source"] == "external-dir"
    assert candidate["status"] == "skipped"
    assert candidate["reason"] == "source-not-agent-created"
    assert result["summary"]["applied"] == 0
    assert sha256_file(skill_file) == original_hash


def test_install_auto_timer_enables_builtin_skill_verify_by_default(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))

    result = install_auto_timer(
        schedule="daily",
        skills_dir=tmp_path / "skills",
        enable=False,
    )

    command = result["command"]
    service_text = Path(result["service_path"]).read_text(encoding="utf-8")
    assert "--verify-command" in command
    assert "hermes_curator_evolver.skill_validate" in command
    assert f"--verify-cwd {tmp_path / 'skills'}" in command
    assert result["verify_command"].endswith(" -m hermes_curator_evolver.skill_validate")
    assert result["verify_cwd"] == str(tmp_path / "skills")
    assert "Environment=PYTHONUNBUFFERED=1" in service_text


def test_install_auto_timer_emits_explicit_core_protection_policy(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))

    result = install_auto_timer(
        schedule="daily",
        skills_dir=tmp_path / "skills",
        enable=False,
        rerank_candidates=True,
        auto_apply_blocklist=("github-*",),
    )

    command = result["command"]
    service_text = Path(result["service_path"]).read_text(encoding="utf-8")
    assert "--apply-low-risk" in command
    assert "--approve-auto-apply" in command
    assert "--protect-core-skills" in command
    assert "--block-auto-apply-skill github-*" in command
    assert result["protect_core_skills"] is True
    assert "--protect-core-skills" in service_text


def test_auto_evolve_json_serializable(tmp_path):
    db = tmp_path / "evidence.sqlite"
    skills = tmp_path / "skills"
    _write_skill(skills, "empty-skill")

    result = run_auto_evolve(AutoEvolveConfig(db_path=db, skills_dir=skills))

    json.dumps(result, ensure_ascii=False, sort_keys=True)


def test_generate_variants_returns_distinct_deterministic_candidates(tmp_path):
    skill_text = _write_skill(tmp_path, "hermes-agent").read_text(encoding="utf-8")
    evidence = [
        {
            "created_at": f"2026-05-{day:02d}T10:00:00+00:00",
            "tool_name": "terminal",
            "is_error": bool(day % 2),
            "result_preview": f"sample {day}",
        }
        for day in range(1, 9)
    ]

    first = generate_variants(
        skill_name="hermes-agent",
        skill_text=skill_text,
        days=7,
        summary={"tool_events": 8, "skill_events": 4, "error_events": 4},
        evidence_rows=evidence,
        count=3,
        generated_at="2026-05-14T12:00:00+00:00",
    )
    second = generate_variants(
        skill_name="hermes-agent",
        skill_text=skill_text,
        days=7,
        summary={"tool_events": 8, "skill_events": 4, "error_events": 4},
        evidence_rows=evidence,
        count=3,
        generated_at="2026-05-14T12:00:00+00:00",
    )

    assert len(first) == 3
    assert [v["name"] for v in first] == [
        "default-verify-first",
        "compact-evidence-first",
        "wide-errors-first",
    ]
    assert [v["prepared"].content for v in first] == [v["prepared"].content for v in second]
    # Different evidence_limit values yield different inline content.
    inline_lengths = {v["prepared"].content for v in first}
    assert len(inline_lengths) > 1


def test_select_winning_variant_prefers_inline_over_spillover():
    variants = [
        {"index": 0, "name": "a", "score": 100, "score_breakdown": [], "size_strategy": "inline", "skipped_reason": None, "content_chars": 1000, "support_files": [], "spec": {}, "prepared": object()},
        {"index": 1, "name": "b", "score": 50, "score_breakdown": [], "size_strategy": "reference-spillover", "skipped_reason": None, "content_chars": 800, "support_files": ["x"], "spec": {}, "prepared": object()},
    ]

    winner = select_winning_variant(variants)

    assert winner["index"] == 0


def test_auto_evolve_default_variants_one_preserves_single_variant_behavior(tmp_path):
    db = tmp_path / "evidence.sqlite"
    store = EvidenceStore(db)
    skills = tmp_path / "skills"
    _write_skill(skills, "hermes-agent")
    store.record_tool_call(
        tool_name="terminal",
        args={"skills": ["hermes-agent"]},
        result={"exit_code": 1, "output": "gateway restart failed"},
        session_id="s1",
    )

    result = run_auto_evolve(
        AutoEvolveConfig(
            db_path=db,
            skills_dir=skills,
            days=30,
            min_evidence=1,
        )
    )

    candidate = result["candidates"][0]
    assert result["config"]["variants"] == 1
    assert candidate["variants_requested"] == 1
    assert len(candidate["variants"]) == 1
    assert candidate["variants"][0]["selected"] is True
    assert candidate["selected_variant"]["name"] == "default-verify-first"


def test_auto_evolve_variants_dry_run_exposes_summaries_and_winner(tmp_path):
    db = tmp_path / "evidence.sqlite"
    store = EvidenceStore(db)
    skills = tmp_path / "skills"
    _write_skill(skills, "hermes-agent")
    for index in range(6):
        store.record_tool_call(
            tool_name="terminal",
            args={"skills": ["hermes-agent"]},
            result={"exit_code": index % 2, "output": f"sample-{index}"},
            session_id=f"s{index}",
        )

    result = run_auto_evolve(
        AutoEvolveConfig(
            db_path=db,
            skills_dir=skills,
            days=30,
            min_evidence=1,
            variants=3,
        )
    )

    candidate = result["candidates"][0]
    assert candidate["variants_requested"] == 3
    assert [v["name"] for v in candidate["variants"]] == [
        "default-verify-first",
        "compact-evidence-first",
        "wide-errors-first",
    ]
    selected = [v for v in candidate["variants"] if v["selected"]]
    assert len(selected) == 1
    assert candidate["selected_variant"]["name"] == selected[0]["name"]
    assert result["config"]["variants"] == 3


def test_auto_evolve_variants_apply_uses_winner_only(tmp_path):
    db = tmp_path / "evidence.sqlite"
    store = EvidenceStore(db)
    skills = tmp_path / "skills"
    backups = tmp_path / "backups"
    skill_file = _write_skill(skills, "store-playbook")
    for index in range(4):
        store.record_tool_call(
            tool_name="terminal",
            args={"skills": ["store-playbook"]},
            result={"exit_code": index, "output": f"sample-{index}"},
            session_id=f"s{index}",
        )

    result = run_auto_evolve(
        AutoEvolveConfig(
            db_path=db,
            skills_dir=skills,
            backup_dir=backups,
            days=30,
            min_evidence=1,
            apply_low_risk=True,
            approve_auto_apply=True,
            variants=3,
        )
    )

    candidate = result["candidates"][0]
    written = skill_file.read_text(encoding="utf-8")
    selected_index = candidate["selected_variant"]["index"]
    winning_content = next(
        variant for variant in candidate["variants"] if variant["index"] == selected_index
    )
    assert candidate["status"] == "applied"
    assert written.count("<!-- curator-evolver:auto:start -->") == 1
    # Each variant has a distinct guidance phrasing — confirm the winner's phrasing made it in.
    if winning_content["spec"]["guidance_style"] == "evidence-first":
        assert "Reuse the matching evidence row above" in written
    elif winning_content["spec"]["guidance_style"] == "errors-first":
        assert "Replay the most recent error-marked evidence" in written
    else:
        assert "When this skill is relevant, check these observed signals" in written


def test_auto_evolve_variants_is_deterministic(tmp_path):
    db = tmp_path / "evidence.sqlite"
    store = EvidenceStore(db)
    skills = tmp_path / "skills"
    _write_skill(skills, "hermes-agent")
    for index in range(5):
        store.record_tool_call(
            tool_name="terminal",
            args={"skills": ["hermes-agent"]},
            result={"exit_code": index, "output": f"sample-{index}"},
            session_id=f"s{index}",
        )

    first = run_auto_evolve(
        AutoEvolveConfig(db_path=db, skills_dir=skills, days=30, min_evidence=1, variants=3)
    )
    second = run_auto_evolve(
        AutoEvolveConfig(db_path=db, skills_dir=skills, days=30, min_evidence=1, variants=3)
    )

    first_summary = [
        {k: v for k, v in variant.items() if k not in {"score_breakdown"}}
        for variant in first["candidates"][0]["variants"]
    ]
    second_summary = [
        {k: v for k, v in variant.items() if k not in {"score_breakdown"}}
        for variant in second["candidates"][0]["variants"]
    ]
    # Index/name/spec/size_strategy/score/selected are stable across runs.
    keys = {"index", "name", "spec", "size_strategy", "score", "selected"}
    assert [{k: v[k] for k in keys} for v in first_summary] == [
        {k: v[k] for k in keys} for v in second_summary
    ]
    assert (
        first["candidates"][0]["selected_variant"]["name"]
        == second["candidates"][0]["selected_variant"]["name"]
    )


def test_auto_evolve_apply_uses_staged_verify_when_pre_verify_command_set(tmp_path):
    db = tmp_path / "evidence.sqlite"
    store = EvidenceStore(db)
    skills = tmp_path / "skills"
    backups = tmp_path / "backups"
    skill_file = _write_skill(skills, "store-playbook")
    store.record_tool_call(
        tool_name="skill_view",
        args={"name": "store-playbook"},
        result={"success": True},
        session_id="s1",
    )

    result = run_auto_evolve(
        AutoEvolveConfig(
            db_path=db,
            skills_dir=skills,
            backup_dir=backups,
            days=30,
            min_evidence=1,
            apply_low_risk=True,
            approve_auto_apply=True,
            pre_verify_command="true",
        )
    )

    candidate = result["candidates"][0]
    verify = candidate["apply_result"]["verify"]
    assert verify["staged"] is True
    stage_names = [stage["name"] for stage in verify["stages"]]
    assert stage_names[0] == "builtin-structural"
    assert "pre-verify-command" in stage_names
    assert candidate["status"] == "applied"
    assert "Auto-curated evidence notes" in skill_file.read_text(encoding="utf-8")
    assert result["config"]["staged_verify"] is True


def test_prune_auto_reference_files_keeps_newest_and_never_touches_handwritten(tmp_path):
    # Roadmap U3: the references/curator-evolver-auto-*.md spill grew without
    # bound across daily runs; pruning keeps the newest N per skill and only
    # ever matches this plugin's own generated naming pattern.
    skill_dir = tmp_path / "demo"
    references = skill_dir / "references"
    references.mkdir(parents=True)
    generated = [
        f"curator-evolver-auto-demo-2026090{day}-120000.md" for day in (1, 2, 3)
    ]
    for name in generated:
        (references / name).write_text("spilled evidence", encoding="utf-8")
    handwritten = references / "handwritten-runbook.md"
    handwritten.write_text("user-authored", encoding="utf-8")
    other_skill = references / "curator-evolver-auto-other-skill-20260901-120000.md"
    other_skill.write_text("different skill slug", encoding="utf-8")

    pruned = auto_evolve.prune_auto_reference_files(skill_dir, "demo", keep=2)

    assert pruned == ["references/curator-evolver-auto-demo-20260901-120000.md"]
    assert (references / generated[0]).exists() is False
    for name in generated[1:]:
        assert (references / name).exists()
    assert handwritten.exists()
    assert other_skill.exists()


def test_prune_auto_reference_files_disable_and_handwritten_protection(tmp_path):
    """U16 / assessment N4: keep=0 disables pruning end-to-end.

    The old ``keep < 0`` guard let keep=0 fall through to ``generated[0:]``
    — pruning every auto reference including the one the same pass just
    wrote — while the CLI help documents 0 as "disable". A non-positive
    bound must prune nothing; only a positive bound prunes, and hand-written
    reference files remain untouchable.
    """

    skill_dir = tmp_path / "demo"

    assert auto_evolve.prune_auto_reference_files(skill_dir, "demo", keep=5) == []

    references = skill_dir / "references"
    references.mkdir(parents=True)
    newest = references / "curator-evolver-auto-demo-20260902-120000.md"
    newest.write_text("spilled evidence", encoding="utf-8")
    handwritten = references / "operator-notes.md"
    handwritten.write_text("hand-written", encoding="utf-8")

    # keep=0 is the documented disable: nothing is pruned, including the
    # reference file a same-day pass just wrote.
    assert auto_evolve.prune_auto_reference_files(skill_dir, "demo", keep=0) == []
    assert newest.exists() is True
    assert auto_evolve.prune_auto_reference_files(skill_dir, "demo", keep=-1) == []
    assert newest.exists() is True

    older = references / "curator-evolver-auto-demo-20260901-120000.md"
    older.write_text("older spill", encoding="utf-8")
    pruned = auto_evolve.prune_auto_reference_files(skill_dir, "demo", keep=1)

    assert pruned == ["references/curator-evolver-auto-demo-20260901-120000.md"]
    assert newest.exists() is True
    assert older.exists() is False
    assert handwritten.exists() is True


def test_auto_evolve_config_defaults_reference_retention():
    assert AutoEvolveConfig().max_reference_files == 5


def test_apply_managed_block_replacement_is_literal_on_second_run():
    """U15 / assessment P1: previews with group references must not crash.

    Any skill that already carries a managed block made the next auto-run
    pass crash with ``re.error: invalid group reference 1`` because the new
    block was passed as a regex replacement template; evidence previews
    legitimately contain ``\\1`` and ``\\g<name>`` spellings. A second run
    with such a block must rewrite the block verbatim, treating it as data.
    """

    first = auto_evolve._apply_managed_block(
        "# Demo\n",
        "<!-- curator-evolver:auto:start -->\nfirst\n<!-- curator-evolver:auto:end -->",
    )
    assert "first" in first

    gnarly = (
        "<!-- curator-evolver:auto:start -->\n"
        "repro: sed -E 's/(x)/\\1/' and \\g<boom> and $1 and \\\\2\n"
        "<!-- curator-evolver:auto:end -->"
    )

    second = auto_evolve._apply_managed_block(first, gnarly)

    assert "first" not in second
    assert "repro: sed -E 's/(x)/\\1/' and \\g<boom> and $1 and \\\\2" in second

    # And the end-to-end path: a preview containing a backreference that is
    # later re-applied onto the already-managed skill must not raise.
    managed_skill = "# Managed\n" + first
    rewritten = auto_evolve._apply_managed_block(managed_skill, gnarly)
    assert rewritten.startswith("# Managed\n")
    assert rewritten.count(auto_evolve._START) == 1


# ---------------------------------------------------------------------------
# Roadmap U17 (assessment P7): schedule grammar validation + unit escaping.
# ---------------------------------------------------------------------------

import pytest


def test_u17_schedule_validation_accepts_canonical_and_oncalendar():
    from hermes_curator_evolver.auto_evolve import _validated_on_calendar

    assert _validated_on_calendar("daily") == "daily"
    assert _validated_on_calendar("Daily") == "daily"
    assert _validated_on_calendar("weekly") == "weekly"
    assert _validated_on_calendar("Mon..Fri 09:00") == "Mon..Fri 09:00"
    assert _validated_on_calendar("*-*-* 03:30:00") == "*-*-* 03:30:00"


@pytest.mark.parametrize(
    "bad",
    [
        "daily\nExecStartPost=/tmp/pwned.sh",
        "daily\r\nUnit=evil.target",
        "daily\n",
        ";comment",
        "daily;Reboot",
        "  ",
        "",
    ],
)
def test_u17_schedule_validation_rejects_directive_injection(bad):
    from hermes_curator_evolver.auto_evolve import _validated_on_calendar

    with pytest.raises(ValueError):
        _validated_on_calendar(bad)


def test_u17_install_auto_timer_refuses_injected_schedule(tmp_path, monkeypatch):
    from hermes_curator_evolver import auto_evolve

    monkeypatch.setattr(auto_evolve, "_scheduler_backend", lambda: "systemd")
    monkeypatch.setattr(auto_evolve, "_systemd_dir", lambda: tmp_path / "units")

    with pytest.raises(ValueError, match="control character"):
        auto_evolve.install_auto_timer(
            schedule="daily\nExecStartPost=/tmp/pwned.sh", enable=True
        )
    # Nothing was written: the rejection happens before any file lands.
    assert not (tmp_path / "units").exists() or not list((tmp_path / "units").iterdir())


def test_u17_quote_systemd_arg_doubles_percent_specifiers():
    from hermes_curator_evolver.auto_evolve import _quote_systemd_arg

    assert _quote_systemd_arg("/tmp/pct%h") == "/tmp/pct%%h"
    assert _quote_systemd_arg("plain") == "plain"
    assert _quote_systemd_arg('quote"d') == '"quote\\"d"'
    assert _quote_systemd_arg("has space") == '"has space"'
    assert _quote_systemd_arg("") == '""'


# ---------------------------------------------------------------------------
# Roadmap U7b: version single-sourcing across plugin surfaces.
# ---------------------------------------------------------------------------


def test_u7b_version_agrees_with_plugin_yaml():
    import re
    from pathlib import Path

    from hermes_curator_evolver import __version__

    manifest = Path(__file__).resolve().parent.parent / "plugin.yaml"
    match = re.search(r"^version:\s*[\"']?([^\"'\n]+)[\"']?\s*$", manifest.read_text(), re.MULTILINE)
    assert match, "plugin.yaml must carry a version"
    assert __version__ == match.group(1).strip()


def test_u7b_version_is_not_the_drifted_literal():
    from hermes_curator_evolver import __version__

    assert __version__ != "0.8.0"


# ---------------------------------------------------------------------------
# Roadmap Q8: bounded clamps warn instead of silently rewriting.
# ---------------------------------------------------------------------------


def test_q8_clamp_warns_naming_old_and_new_value(caplog):
    import logging

    from hermes_curator_evolver.auto_evolve import _bounded

    with caplog.at_level(logging.WARNING, logger="hermes_curator_evolver.auto_evolve"):
        assert _bounded(99999, minimum=1, maximum=3650, label="days") == 3650
    assert any("clamped from 99999 to 3650" in rec.message for rec in caplog.records)

    caplog.clear()
    with caplog.at_level(logging.WARNING, logger="hermes_curator_evolver.auto_evolve"):
        assert _bounded(0, minimum=1, maximum=3650, label="days") == 1
    assert any("clamped from 0 to 1" in rec.message for rec in caplog.records)


def test_q8_in_range_value_does_not_warn(caplog):
    import logging

    from hermes_curator_evolver.auto_evolve import _bounded

    with caplog.at_level(logging.WARNING, logger="hermes_curator_evolver.auto_evolve"):
        assert _bounded(30, minimum=1, maximum=3650, label="days") == 30
    assert not caplog.records


def test_u17_quote_systemd_arg_rejects_control_characters():
    from hermes_curator_evolver.auto_evolve import _quote_systemd_arg

    for hostile in ["daily\nExecStartPost=/tmp/pwned.sh", "a\rb", "a\tb", "a\x00b"]:
        with pytest.raises(ValueError, match="control characters"):
            _quote_systemd_arg(hostile)


def test_u17_install_rejects_control_characters_in_embedded_paths(tmp_path, monkeypatch):
    from hermes_curator_evolver import auto_evolve

    monkeypatch.setattr(auto_evolve, "_scheduler_backend", lambda: "systemd")
    monkeypatch.setattr(auto_evolve, "_systemd_dir", lambda: tmp_path / "units")

    with pytest.raises(ValueError, match="control characters"):
        auto_evolve.install_auto_timer(
            schedule="daily", skills_dir=str(tmp_path) + "\nExecStartPost=/tmp/pwned.sh"
        )
    assert not (tmp_path / "units").exists()
