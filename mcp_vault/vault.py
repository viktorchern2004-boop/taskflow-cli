"""Local, git-synchronized Obsidian vault operations behind the MCP boundary.

The server process, not the agent workspace, gets TASKFLOW_VAULT_PATH.
"""
from __future__ import annotations

import os
import re
import subprocess
from datetime import date
from pathlib import Path

TYPE_DIRS = {
    "concept": "Concepts",
    "component": "Components",
    "decision": "Decisions",
    "glossary": "Glossary",
}


def _vault_root(vault_path: str | None = None) -> Path:
    value = vault_path or os.environ.get("TASKFLOW_VAULT_PATH")
    if not value:
        raise ValueError("TASKFLOW_VAULT_PATH is not configured")
    root = Path(value).expanduser().resolve()
    if not root.is_dir():
        raise ValueError("The configured Obsidian vault directory does not exist")
    return root


def _safe_title(title: str) -> str:
    name = title.strip()
    if not re.fullmatch(r"[\w][\w .-]{0,79}", name, re.UNICODE):
        raise ValueError("Invalid title: use letters, numbers, spaces, _ or - (max 80)")
    if ".." in name or name.endswith("."):
        raise ValueError("Invalid title")
    return name


def _git(root: Path, *args: str, check: bool = True) -> str:
    run = subprocess.run(
        ["git", "-C", str(root), *args], text=True, capture_output=True,
        encoding="utf-8", errors="replace", check=False,
    )
    if check and run.returncode != 0:
        raise RuntimeError("Git operation failed: " + " ".join(args[:2]) +
                           ". Check repository, credentials and branch in terminal.")
    return run.stdout.strip() if run.returncode == 0 else ""


def _branch(root: Path, branch: str) -> None:
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._/-]*", branch) or ".." in branch:
        raise ValueError("Invalid vault branch name")
    if branch in {"main", "master"}:
        raise ValueError("Direct agent writes to main/master are prohibited")
    if not (root / ".git").exists():
        raise ValueError("Vault must be a separate git clone")
    _git(root, "fetch", "origin")
    local = _git(root, "show-ref", "--verify", f"refs/heads/{branch}", check=False)
    remote = _git(root, "show-ref", "--verify", f"refs/remotes/origin/{branch}", check=False)
    if local:
        _git(root, "switch", branch)
    elif remote:
        _git(root, "switch", "-c", branch, "--track", f"origin/{branch}")
    else:
        _git(root, "switch", "-c", branch, "origin/main")
    if remote:
        _git(root, "pull", "--ff-only", "origin", branch)


def search_notes(query: str, limit: int = 5, vault_path: str | None = None) -> list[dict]:
    """Return ranked lexical matches (semantic search replaces this in PR7)."""
    root = _vault_root(vault_path)
    phrase = query.strip().casefold()
    if not phrase:
        return []
    if not 1 <= limit <= 20:
        raise ValueError("limit must be between 1 and 20")
    words = set(re.findall(r"\w+", phrase))
    matches = []
    for note in root.rglob("*.md"):
        if ".git" in note.parts or ".obsidian" in note.parts:
            continue
        if note.is_symlink() or not note.is_file():
            continue
        text = note.read_text(encoding="utf-8")
        title = note.stem.casefold()
        body = text.casefold()
        score = 8 * (phrase in title) + 4 * (phrase in body)
        score += sum(3 * (word in title) + (word in body) for word in words)
        if score:
            matches.append({"title": note.stem, "path": note.relative_to(root).as_posix(),
                            "score": score, "excerpt": text[:700]})
    return sorted(matches, key=lambda x: (-x["score"], x["path"]))[:limit]


def get_note(title: str, vault_path: str | None = None) -> dict:
    """Read a note by unique filename (without .md)."""
    root = _vault_root(vault_path)
    target = _safe_title(title)
    files = [p for p in root.rglob("*.md") if p.stem.casefold() == target.casefold()
             and not p.is_symlink() and ".git" not in p.parts]
    if not files:
        return {"found": False, "title": target}
    if len(files) > 1:
        return {"found": False, "error": "ambiguous_title", "title": target}
    return {"found": True, "title": files[0].stem,
            "path": files[0].relative_to(root).as_posix(),
            "content": files[0].read_text(encoding="utf-8")}


def ingest_note(title: str, type: str, content: str, links: list[str] | None = None,
                vault_path: str | None = None, branch: str | None = None) -> dict:
    """Create/update an MCP-owned note, commit and push to a safe branch.

    Repeated calls are idempotent; human-authored notes are protected.
    """
    root = _vault_root(vault_path)
    name = _safe_title(title)
    if type not in TYPE_DIRS:
        raise ValueError("type must be concept, component, decision or glossary")
    if not content.strip() or len(content) > 30000:
        raise ValueError("content must contain 1..30000 non-blank characters")
    checked_links = [_safe_title(item) for item in (links or [])]
    if len(checked_links) > 30:
        raise ValueError("Too many links")
    checked_links = list(dict.fromkeys(checked_links))
    target_branch = branch or os.environ.get("VAULT_GIT_BRANCH", "pr3-mcp-ingestion")
    _branch(root, target_branch)
    path = root / TYPE_DIRS[type] / f"{name}.md"
    path.parent.mkdir(exist_ok=True)
    if path.is_symlink():
        raise ValueError("Refusing to write through symlink")
    previous = path.read_text(encoding="utf-8") if path.exists() else ""
    if previous and "managed_by: vault-mcp" not in previous.partition("---")[2].partition("---")[0]:
        raise ValueError("Refusing to overwrite a human-authored note")
    changed = _git(root, "status", "--porcelain", "--", path.relative_to(root).as_posix())
    if changed:
        raise RuntimeError("Note has uncommitted local changes; resolve them first")
    old_date = re.search(r"(?m)^created: (\d{4}-\d{2}-\d{2})$", previous)
    created = old_date.group(1) if old_date else date.today().isoformat()
    body = content.strip() + "\n"
    if checked_links:
        body += "\n## Пов'язані нотатки\n" + "\n".join(f"- [[{link}]]" for link in checked_links) + "\n"
    note_text = (f"---\ntype: {type}\ncreated: {created}\n"
                 f"tags: [taskflow, {type}]\nmanaged_by: vault-mcp\n---\n\n"
                 f"# {name}\n\n{body}")
    relative = path.relative_to(root).as_posix()
    if previous == note_text:
        return {"status": "unchanged", "path": relative, "branch": target_branch}
    path.write_text(note_text, encoding="utf-8")
    _git(root, "add", "--", relative)
    _git(root, "commit", "--only", "-m", f"docs(vault): upsert {name}", "--", relative)
    _git(root, "push", "-u", "origin", target_branch)
    return {"status": "updated" if previous else "created", "path": relative,
            "branch": target_branch, "commit": _git(root, "rev-parse", "--short", "HEAD")}
