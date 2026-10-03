"""U119 (cycle-13, assess F3): a TRUNCATED PEM paste redacts the body, not
just the marker line.

The U95 ``pem-private-key-block`` arm needs BEGIN *and* END, so a paste
cut mid-key (BEGIN + base64 body, no END) matched only the header arm —
``scrub_text`` replaced the marker line while the ENTIRE base64 body
survived verbatim (assess probe: a 1003-char body emerged intact). The new
``pem-private-key-truncated`` arm redacts from the marker through the
first blank line or end-of-input, but only when the line after the marker
is real key-body material (a 20+ char base64 run), so prose that merely
mentions the marker keeps its surrounding text. Strictly widening: the
full-block arm and the bare-header arm keep their U95 contracts (pinned in
test_cycle9_hygiene_readers_classifier.py).

Adversarial bodies are constructed PROGRAMMATICALLY with length assertions
(cycle-12 review lesson: hand-counted probe constants produce false
findings — the battery asserts the lengths it reasons about).
"""

from __future__ import annotations

from hermes_curator_evolver.hygiene import count_credentials, scrub_text

BEGIN = "-----BEGIN RSA PRIVATE KEY-----"
END = "-----END RSA PRIVATE KEY-----"

# 64-char base64-alphabet line, built programmatically.
_BODY_LINE = "MII" + "A" * 61
assert len(_BODY_LINE) == 64


def _body(lines: int) -> str:
    body = "\n".join([_BODY_LINE] * lines)
    assert len(body) == 64 * lines + (lines - 1)
    return body


def test_u119_truncated_pem_redacts_body_to_end_of_input():
    """The assess F3 shape: BEGIN + body, no END — the whole body goes."""
    raw = BEGIN + "\n" + _body(16)  # 16 lines, 1039 chars of body
    text, hits = scrub_text(raw)

    assert "[REDACTED:pem-private-key-truncated]" in text
    assert _BODY_LINE not in text
    assert "A" * 61 not in text
    assert raw not in text
    assert hits == 1


def test_u119_truncated_pem_stops_at_first_blank_line():
    """A paste followed by prose after a blank line: the prose survives,
    the truncated key body does not."""
    raw = BEGIN + "\n" + _body(3) + "\n\nprose after the paste\n"
    text, hits = scrub_text(raw)

    assert "[REDACTED:pem-private-key-truncated]" in text
    assert _BODY_LINE not in text
    assert "prose after the paste" in text
    assert hits == 1


def test_u119_full_block_redaction_is_unchanged():
    """Strictly-widening check: BEGIN+body+END still takes the U95 block
    arm (one redaction, the END included), never the truncated arm."""
    raw = BEGIN + "\n" + _body(3) + "\n" + END
    text, hits = scrub_text(raw)

    assert "[REDACTED:pem-private-key-block]" in text
    assert "[REDACTED:pem-private-key-truncated]" not in text
    assert _BODY_LINE not in text
    assert hits == 1


def test_u119_prose_mentioning_the_marker_survives():
    """Differential pins: prose that merely mentions "BEGIN PRIVATE KEY"
    without base64 body material must not gain the widened arm."""

    # Inline mention — no newline after the marker at all.
    prose = (
        "Docs say every PEM file starts with the line "
        "-----BEGIN PRIVATE KEY----- before base64 data."
    )
    text, hits = scrub_text(prose)
    assert "[REDACTED:pem-private-key-header]" in text
    assert "[REDACTED:pem-private-key-truncated]" not in text
    assert "before base64 data" in text
    assert hits == 1

    # Newline after the marker but the next line is words, not a 20+ char
    # base64 run — the body-material lookahead is the discriminator.
    prose_nl = (
        "-----BEGIN PRIVATE KEY-----\n"
        "then comes the base64 body on later lines.\n"
    )
    text, hits = scrub_text(prose_nl)
    assert "[REDACTED:pem-private-key-header]" in text
    assert "[REDACTED:pem-private-key-truncated]" not in text
    assert "then comes the base64 body on later lines." in text
    assert hits == 1


def test_u119_truncated_pem_is_detected_by_count_credentials():
    """The detection-only companion (skill_validate publish gate) sees the
    truncated paste as credential-shaped — one occurrence per arm, same
    double-count shape a full block already had (block + header)."""
    raw = BEGIN + "\n" + _body(4)
    assert count_credentials(raw) >= 1
    # ...and a bare marker alone still reads as exactly the header shape.
    assert count_credentials("leaked: " + BEGIN) == 1
