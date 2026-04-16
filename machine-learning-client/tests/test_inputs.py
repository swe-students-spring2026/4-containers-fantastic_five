"""Tests for the CMInputs model."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from inputs import CMInputs  # pylint: disable=wrong-import-position,import-error


def test_cminputs_defaults():
    """CMInputs should default all optional fields to None."""
    data = CMInputs()
    assert data.session_id is None
    assert data.intended_university is None
    assert data.user_essay is None
    assert data.user_interview_response is None
    assert data.essay_file_name is None
    assert data.notes is None
    assert data.sat_score is None
    assert data.gpa is None
    assert data.essay_pdf_bytes is None
    assert data.result is None


def test_cminputs_accepts_values():
    """CMInputs should store explicitly provided values."""
    data = CMInputs(
        session_id="123",
        intended_university="NYU",
        user_essay="My essay",
        user_interview_response="My response",
        essay_file_name="essay.pdf",
        notes="Strong extracurriculars",
        sat_score=1500,
        gpa=4.0,
        essay_pdf_bytes=b"abc",
        result="Done",
    )

    assert data.session_id == "123"
    assert data.intended_university == "NYU"
    assert data.user_essay == "My essay"
    assert data.user_interview_response == "My response"
    assert data.essay_file_name == "essay.pdf"
    assert data.notes == "Strong extracurriculars"
    assert data.sat_score == 1500
    assert data.gpa == 4.0
    assert data.essay_pdf_bytes == b"abc"
    assert data.result == "Done"