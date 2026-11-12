import subprocess
import pytest
from mcp_vault.vault import search_notes, get_note, ingest_note

def git(directory, *args):
    return subprocess.run(["git", "-C", str(directory), *args], capture_output=True, text=True, check=True).stdout.strip()

@pytest.fixture
def vault(tmp_path):
    remote = tmp_path / "remote.git"
    remote.mkdir()
    git(remote, "init", "--bare", "--initial-branch=main")
    origin = tmp_path / "source"
    origin.mkdir()
    git(origin, "init", "--initial-branch=main")
    git(origin, "config", "user.email", "test@example.com")
    git(origin, "config", "user.name", "Test")
    (origin / "Concepts").mkdir()
    (origin / "Concepts" / "Task.md").write_text("# Task\nA work item with status and priority", encoding="utf-8")
    git(origin, "add", ".")
    git(origin, "commit", "-m", "seed")
    git(origin, "remote", "add", "origin", str(remote))
    git(origin, "push", "-u", "origin", "main")
    clone = tmp_path / "vault"
    subprocess.run(["git", "clone", str(remote), str(clone)], check=True, capture_output=True)
    git(clone, "config", "user.email", "test@example.com")
    git(clone, "config", "user.name", "Test")
    return clone, remote

def test_search_and_get(vault):
    clone, _ = vault
    found = search_notes("priority", vault_path=str(clone))
    assert found and found[0]["path"] == "Concepts/Task.md"
    assert get_note("Task", vault_path=str(clone))["found"] is True
    assert get_note("unknown", vault_path=str(clone))["found"] is False

def test_idempotent_commit_push_and_update(vault):
    clone, remote = vault
    params = dict(title="ADR-MCP", type="decision", content="Connect notes with MCP.",
                  links=["Task"], vault_path=str(clone))
    first = ingest_note(**params)
    assert first["status"] == "created"
    before = git(clone, "rev-parse", "HEAD")
    assert ingest_note(**params)["status"] == "unchanged"
    assert git(clone, "rev-parse", "HEAD") == before
    assert ingest_note(**{**params, "content": "MCP is the sole gateway."})["status"] == "updated"
    assert git(clone, "rev-parse", "HEAD") != before
    assert git(remote, "show-ref", "refs/heads/pr3-mcp-ingestion")
    data = get_note("ADR-MCP", vault_path=str(clone))
    assert data["content"].count("[[Task]]") == 1

def test_guards(vault):
    clone, _ = vault
    with pytest.raises(ValueError):
        ingest_note("../escape", "decision", "content", vault_path=str(clone))
    with pytest.raises(ValueError):
        ingest_note("A", "unknown", "content", vault_path=str(clone))
    with pytest.raises(ValueError):
        ingest_note("X", "decision", "content", vault_path=str(clone), branch="main")
    with pytest.raises(ValueError, match="human-authored"):
        ingest_note("Task", "concept", "overwrite", vault_path=str(clone))
