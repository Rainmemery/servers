# -*- coding: utf-8 -*-
"""Regression tests for the git_show diff header (issue #5107).

git_show must emit a git-compatible unified-diff header - a `diff --git`
line plus `a/` and `b/` prefixed `---`/`+++` paths - so that its output
matches `git show` and can be consumed by `git apply` / `patch`.
"""
from pathlib import Path

import git

from mcp_server_git.server import git_show


def _init_repo(path: Path) -> git.Repo:
    repo = git.Repo.init(path)
    with repo.config_writer() as cw:
        cw.set_value("user", "name", "Test")
        cw.set_value("user", "email", "test@example.com")
        cw.set_value("core", "autocrlf", "false")
    return repo


def _commit(repo: git.Repo, message: str) -> git.Commit:
    repo.git.add(A=True)
    return repo.index.commit(message)


def test_git_show_modified_file_header(tmp_path: Path):
    repo = _init_repo(tmp_path)
    (tmp_path / "demo.txt").write_text("line1\nline2\n")
    _commit(repo, "initial")
    (tmp_path / "demo.txt").write_text("line1\nline2 modified\nline3\n")
    second = _commit(repo, "modify demo")

    out = git_show(repo, second.hexsha)

    assert "diff --git a/demo.txt b/demo.txt" in out
    assert "--- a/demo.txt" in out
    assert "+++ b/demo.txt" in out


def test_git_show_added_file_header(tmp_path: Path):
    repo = _init_repo(tmp_path)
    (tmp_path / "new.txt").write_text("fresh\n")
    first = _commit(repo, "add new.txt")

    out = git_show(repo, first.hexsha)

    # The diff --git line always uses the real paths (a/new.txt b/new.txt),
    # while the ---/+++ header lines use /dev/null for the missing side.
    assert "diff --git a/new.txt b/new.txt" in out
    assert "--- /dev/null" in out
    assert "+++ b/new.txt" in out


def test_git_show_deleted_file_header(tmp_path: Path):
    repo = _init_repo(tmp_path)
    (tmp_path / "old.txt").write_text("going away\n")
    _commit(repo, "add old.txt")
    repo.git.rm("old.txt")
    second = _commit(repo, "delete old.txt")

    out = git_show(repo, second.hexsha)

    assert "diff --git a/old.txt b/old.txt" in out
    assert "--- a/old.txt" in out
    assert "+++ /dev/null" in out
