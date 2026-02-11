"""Tests for filesystem utilities."""

from __future__ import annotations

from pathlib import Path

from src.utils.filesystem import copy_template, replace_in_file


class TestReplaceInFile:
    """Tests for replace_in_file."""

    def test_replaces_tokens(self, tmp_path: Path) -> None:
        f = tmp_path / "test.txt"
        f.write_text("Hello {{NAME}}, welcome to {{PLACE}}.")
        count = replace_in_file(
            f,
            [("{{NAME}}", "Alice"), ("{{PLACE}}", "Wonderland")],
            dry_run=False,
        )
        assert count == 2
        assert f.read_text() == "Hello Alice, welcome to Wonderland."

    def test_dry_run_does_not_modify(self, tmp_path: Path) -> None:
        f = tmp_path / "test.txt"
        original = "Hello {{NAME}}"
        f.write_text(original)
        replace_in_file(f, [("{{NAME}}", "Alice")], dry_run=True)
        assert f.read_text() == original

    def test_missing_file_returns_zero(self, tmp_path: Path) -> None:
        f = tmp_path / "nonexistent.txt"
        count = replace_in_file(f, [("a", "b")], dry_run=False)
        assert count == 0

    def test_no_matching_tokens_returns_zero(self, tmp_path: Path) -> None:
        f = tmp_path / "test.txt"
        f.write_text("no tokens here")
        count = replace_in_file(f, [("{{MISSING}}", "value")], dry_run=False)
        assert count == 0

    def test_multiple_occurrences_counted(self, tmp_path: Path) -> None:
        f = tmp_path / "test.txt"
        f.write_text("{{X}} and {{X}} and {{X}}")
        count = replace_in_file(f, [("{{X}}", "Y")], dry_run=False)
        assert count == 3
        assert f.read_text() == "Y and Y and Y"


class TestCopyTemplate:
    """Tests for copy_template."""

    def test_copies_directory_contents(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "file.txt").write_text("content")
        subdir = src / "sub"
        subdir.mkdir()
        (subdir / "nested.txt").write_text("nested")
        dst = tmp_path / "dst"

        copy_template(src, dst, dry_run=False)

        assert (dst / "file.txt").read_text() == "content"
        assert (dst / "sub" / "nested.txt").read_text() == "nested"

    def test_dry_run_does_not_copy(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        dst = tmp_path / "dst"

        copy_template(src, dst, dry_run=True)
        assert not dst.exists()
