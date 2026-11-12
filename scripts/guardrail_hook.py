"""TaskFlow PR4 Copilot pre-tool-use guardrail. Reads JSON stdin, emits JSON stdout."""
from __future__ import annotations

import json
import re
import sys
from typing import Any

_COMMAND_TOOLS = {"bash", "powershell", "terminal", "run_in_terminal", "run_command", "execute", "run_terminal_command"}
_WRITE_TOOLS = {"create", "edit", "write", "apply_patch", "str_replace_editor", "create_file", "write_file", "replace_string_in_file"}


def _arguments(event: dict[str, Any]) -> dict[str, Any]:
    value = event.get("toolArgs", event.get("tool_input", {}))
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return {"command": value}
        return decoded if isinstance(decoded, dict) else {}
    return value if isinstance(value, dict) else {}


def _decision(outcome: str, rule: str, reason: str) -> dict[str, str]:
    return {"permissionDecision": outcome,
            "permissionDecisionReason": f"TaskFlow {rule}: {reason}"}


def _paths_from_args(args: dict[str, Any]) -> list[str]:
    result = []
    for key in ("path", "filePath", "file_path", "target", "filename"):
        value = args.get(key)
        if isinstance(value, str):
            result.append(value.replace("\\", "/"))
    return result


def _push_arguments(command: str) -> list[str]:
    return re.findall(r"(?i)\bgit\s+(?:-C\s+\S+\s+)?push\b([^\r\n;&|]*)", command)


def check(event: dict[str, Any]) -> dict[str, str]:
    """Return deny/ask for covered operations, or {} for ordinary permissions."""
    tool = str(event.get("toolName", event.get("tool_name", ""))).lower()
    args = _arguments(event)
    is_command = tool in _COMMAND_TOOLS or tool.endswith("run_in_terminal")
    is_write = tool in _WRITE_TOOLS or tool.endswith("apply_patch")
    command = ""
    if is_command:
        for key in ("command", "cmd", "script", "shellCommand", "shell_command"):
            value = args.get(key)
            if isinstance(value, str):
                command = value
                break
    paths = _paths_from_args(args) if is_write else []

    if is_command:
        for tail in _push_arguments(command):
            fields = tail.lower().split()
            if "--force" in fields or "-f" in fields or "--force-with-lease" in fields:
                return _decision("deny", "B02", "Force-push is prohibited")
            if any(item in {"main", "master", "refs/heads/main", "refs/heads/master"}
                   or item.endswith(":main") or item.endswith(":master") for item in fields):
                return _decision("deny", "B01", "Direct push to main/master is prohibited; use a PR")
        if re.search(r"(?i)\bgit\s+(?:-C\s+\S+\s+)?reset\b[^\r\n;&|]*--hard\b", command) \
           or re.search(r"(?i)\bgit\s+(?:-C\s+\S+\s+)?clean\b[^\r\n;&|]*\s-[a-z]*f", command):
            return _decision("deny", "B02", "Destructive git reset/clean is prohibited")
        if re.search(r"(?i)(?:rm\s+-[a-z]*r[a-z]*f|rm\s+-[a-z]*f[a-z]*r|remove-item\b[^\r\n;&|]*-recurse\b)[^\r\n;&|]*\.git(?:[\\/\s]|$)", command):
            return _decision("deny", "B02", "Deleting .git is prohibited")
        if re.search(r"(?i)\b(?:rm|del|erase|remove-item)\b[^\r\n;&|]*taskflow-knowledge-base[\\/]Decisions[\\/]", command):
            return _decision("deny", "B03", "Deleting vault decisions is prohibited")
        if re.search(r"(?i)taskflow-knowledge-base[\\/]", command) and (
            re.search(r"(?i)\b(?:set-content|add-content|out-file|remove-item|rm|del|erase|tee-object)\b", command)
            or re.search(r"(?m)(?:^|[^<])>(?:>|\s)", command)
        ):
            return _decision("deny", "B03", "Direct shell writes to vault are prohibited")

    for path in paths:
        canonical = path.lower()
        if canonical.startswith("./"):
            canonical = canonical[2:]
        if re.search(r"(?:^|/)taskflow-knowledge-base/", canonical):
            return _decision("deny", "B03", "Direct edits to vault must use MCP")
        basename = canonical.rsplit("/", 1)[-1]
        if basename in {".env", "credentials.json", "id_rsa", "id_ed25519", "secrets.json"} \
           or basename.endswith((".pem", ".p12", ".key")):
            return _decision("deny", "B04", "Do not write credentials/private keys")

    if is_write:
        for path in paths:
            canonical = path.lower().replace("\\", "/").lstrip("./")
            if canonical.startswith("src/"):
                return _decision("ask", "W01", "Changes to src/ require approval")
            if canonical in {"pyproject.toml", "requirements.txt", "requirements-dev.txt"}:
                return _decision("ask", "W02", "Dependency changes require approval")
    if is_command and (_push_arguments(command) or re.search(r"(?i)\bgit\s+(?:-C\s+\S+\s+)?commit\b", command)):
        return _decision("ask", "W03", "Git commit/push requires approval")
    if "ingest_note" in tool:
        return _decision("ask", "W04", "Writing vault notes requires approval")
    return {}


def main() -> int:
    try:
        event = json.load(sys.stdin)
        if not isinstance(event, dict):
            raise ValueError("Hook event must be an object")
        result = check(event)
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        result = _decision("deny", "B00", f"Invalid hook payload: {type(exc).__name__}")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
