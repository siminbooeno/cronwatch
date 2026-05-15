"""Tests for cronwatch.job_notes."""
from __future__ import annotations

import os
import pytest

from cronwatch.job_notes import add_note, get_notes, delete_note, clear_notes


@pytest.fixture()
def state_dir(tmp_path):
    return str(tmp_path)


def test_get_notes_empty(state_dir):
    assert get_notes(state_dir, "backup") == []


def test_add_note_returns_record(state_dir):
    rec = add_note(state_dir, "backup", "First note")
    assert rec["job"] == "backup"
    assert rec["text"] == "First note"
    assert rec["author"] is None
    assert "id" in rec
    assert "created_at" in rec


def test_add_note_with_author(state_dir):
    rec = add_note(state_dir, "backup", "Check logs", author="alice")
    assert rec["author"] == "alice"


def test_add_note_persisted(state_dir):
    add_note(state_dir, "backup", "Note A")
    notes = get_notes(state_dir, "backup")
    assert len(notes) == 1
    assert notes[0]["text"] == "Note A"


def test_multiple_notes_ordered(state_dir):
    add_note(state_dir, "backup", "First")
    add_note(state_dir, "backup", "Second")
    notes = get_notes(state_dir, "backup")
    assert len(notes) == 2
    assert notes[0]["text"] == "First"
    assert notes[1]["text"] == "Second"


def test_notes_isolated_per_job(state_dir):
    add_note(state_dir, "job_a", "Note for A")
    assert get_notes(state_dir, "job_b") == []


def test_delete_note_returns_true(state_dir):
    rec = add_note(state_dir, "backup", "To delete")
    result = delete_note(state_dir, "backup", rec["id"])
    assert result is True
    assert get_notes(state_dir, "backup") == []


def test_delete_note_missing_returns_false(state_dir):
    result = delete_note(state_dir, "backup", "nonexistent-id")
    assert result is False


def test_delete_note_leaves_others(state_dir):
    r1 = add_note(state_dir, "backup", "Keep")
    r2 = add_note(state_dir, "backup", "Remove")
    delete_note(state_dir, "backup", r2["id"])
    notes = get_notes(state_dir, "backup")
    assert len(notes) == 1
    assert notes[0]["id"] == r1["id"]


def test_clear_notes_returns_count(state_dir):
    add_note(state_dir, "backup", "A")
    add_note(state_dir, "backup", "B")
    count = clear_notes(state_dir, "backup")
    assert count == 2
    assert get_notes(state_dir, "backup") == []


def test_clear_notes_empty_returns_zero(state_dir):
    assert clear_notes(state_dir, "backup") == 0


def test_note_file_uses_safe_name(state_dir):
    add_note(state_dir, "my/job", "test")
    files = os.listdir(state_dir)
    assert any("notes_" in f for f in files)
    assert all("/" not in f for f in files)
