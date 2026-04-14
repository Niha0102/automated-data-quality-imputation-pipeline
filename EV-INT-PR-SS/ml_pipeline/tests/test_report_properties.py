"""Property 8: Report serialization round-trip — deserialize(serialize(report)) == report."""
from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from pipeline.report_generator import Report, serialize_report, deserialize_report


# ── Strategies ────────────────────────────────────────────────────────────────

_text = st.text(min_size=0, max_size=50)
_opt_float = st.one_of(st.none(), st.floats(0.0, 100.0, allow_nan=False, allow_infinity=False))
_str_list = st.lists(_text, max_size=5)


def _report_strategy():
    return st.builds(
        Report,
        job_id=st.uuids().map(str),
        dataset_id=st.uuids().map(str),
        user_id=st.uuids().map(str),
        quality_score=_opt_float,
        completeness=_opt_float,
        consistency=_opt_float,
        accuracy=_opt_float,
        issues=_str_list,
        fixes=_str_list,
        narrative=_text,
    )


# ── Property 8: Serialization round-trip ─────────────────────────────────────

@given(_report_strategy())
@settings(max_examples=50)
def test_serialize_deserialize_roundtrip(report: Report):
    """Property 8: deserialize(serialize(report)) == report."""
    serialized = serialize_report(report)
    recovered = deserialize_report(serialized)

    assert recovered.job_id == report.job_id
    assert recovered.dataset_id == report.dataset_id
    assert recovered.user_id == report.user_id
    assert recovered.issues == report.issues
    assert recovered.fixes == report.fixes
    assert recovered.narrative == report.narrative

    # Float fields: compare with tolerance for None
    for field in ("quality_score", "completeness", "consistency", "accuracy"):
        orig = getattr(report, field)
        rec = getattr(recovered, field)
        if orig is None:
            assert rec is None
        else:
            assert abs(rec - orig) < 1e-6, f"{field}: {rec} != {orig}"


# ── Unit tests ────────────────────────────────────────────────────────────────

def test_serialize_produces_valid_json():
    """serialize_report should produce a valid JSON string."""
    import json
    report = Report(job_id="j1", dataset_id="d1", user_id="u1")
    s = serialize_report(report)
    parsed = json.loads(s)
    assert parsed["job_id"] == "j1"


def test_deserialize_restores_lists():
    """Lists (issues, fixes) should survive round-trip."""
    report = Report(
        job_id="j2", dataset_id="d2", user_id="u2",
        issues=["missing values", "outliers"],
        fixes=["imputed", "capped"],
    )
    recovered = deserialize_report(serialize_report(report))
    assert recovered.issues == ["missing values", "outliers"]
    assert recovered.fixes == ["imputed", "capped"]


def test_deserialize_restores_none_fields():
    """None fields should remain None after round-trip."""
    report = Report(job_id="j3", dataset_id="d3", user_id="u3", quality_score=None)
    recovered = deserialize_report(serialize_report(report))
    assert recovered.quality_score is None


def test_pdf_generation_returns_bytes():
    """generate_pdf should return bytes (even if reportlab is absent)."""
    from pipeline.report_generator import generate_pdf
    report = Report(
        job_id="j4", dataset_id="d4", user_id="u4",
        quality_score=85.5, completeness=90.0, consistency=80.0, accuracy=88.0,
        issues=["test issue"], fixes=["test fix"], narrative="Test narrative.",
    )
    result = generate_pdf(report)
    assert isinstance(result, bytes)
    assert len(result) > 0
