"""Tests for secret scrubbing (hygiene layer)."""

from hermes_curator_evolver.hygiene import scrub_text

AWS_VALUE = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"  # 40-char base64


def _scrubbed(text: str) -> bool:
    scrubbed_text, _count = scrub_text(text)
    return "wJalr" not in scrubbed_text


# --- label backstop variants -------------------------------------------------
def test_label_variants_scrubbed():
    cases = [
        "SECRET_KEY=django-hunter2secret",
        "secret_key=s3cr3tvalue9",
        "API_TOKEN=tok-998877abcdef",
        "password1: changeme2024xyz",
        "password: hunter2secret99",
        "token: abcdef12345678",
    ]
    for text in cases:
        assert "hunter" not in scrub_text(text)[0] or _scrubbed(text)
        # value must not survive
        value = text.split("=", 1)[-1].split(":", 1)[-1].strip()
        assert value not in scrub_text(text)[0], text


# --- AWS tail escapes ---------------------------------------------------
# The aws-secret-key arm is LABEL-GUARDED (U95): a bare 40-char base64 run
# in prose stays intact on purpose; the scrub fires on "aws … secret … key"
# labels. The U108 defect was the trailing \b: a 40-char value ENDING in
# '/'/'+'/'=' failed the word boundary even with the label present.
def test_aws_tail_slash_scrubbed():
    value = AWS_VALUE[:-1] + "/"
    assert _scrubbed(f"aws secret access key: {value}")


def test_aws_tail_plus_scrubbed():
    value = AWS_VALUE[:-1] + "+"
    assert _scrubbed(f"aws secret access key: {value}")


def test_aws_tail_equals_scrubbed():
    value = AWS_VALUE[:-1] + "="
    assert _scrubbed(f"AWS SECRET_KEY = {value}")


def test_aws_overlong_not_scrubbed():
    # label + 44-char run stays out: the arm is exact-40 by design
    # (github-pat owns 44), so a longer run is not this credential shape
    text = f"aws secret access key: {AWS_VALUE}abcd"
    assert not _scrubbed(text)


def test_aws_bare_value_without_label_stays_intact():
    # the label guard is deliberate: bare base64 in prose is not a secret
    assert not _scrubbed(f"note the hash wJalr prefix: {AWS_VALUE}")


# --- google-api-key length variants ---------------------------------------
def test_google_key_36_scrubbed():
    text = "google AIzaSyA1234567890abcdefghijklmnopqrstuv"
    assert "AIzaSy" not in scrub_text(text)[0]


def test_google_key_35_underscore_tail_scrubbed():
    # 35 chars after prefix, tail '_' previously broke the trailing \b
    text = "google AIza" + "01234567890123456789012345678901234_"
    assert "AIza" not in scrub_text(text)[0]


# --- guards: benign prose must stay intact ---------------------------------
def test_benign_prose_untouched():
    text = "the password rotation task completed without issues"
    scrubbed_text, count = scrub_text(text)
    assert "password rotation task" in scrubbed_text
    assert count == 0


def test_short_value_not_scrubbed():
    # label present but value lacks a digit and is short — prose, not a secret
    scrubbed_text, count = scrub_text("token = see-below")
    assert count == 0
    assert "see-below" in scrubbed_text


def test_no_label_no_scrub():
    # bare 40-char run without a recognized label/prefix context
    scrubbed_text, count = scrub_text(f"id {AWS_VALUE}x")  # 41 chars, no label
    assert count == 0
