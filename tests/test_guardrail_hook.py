"""TaskFlow PR4 policy fixtures: allow/warn/block + runtime protocol."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "guardrail_hook.py"
spec = importlib.util.spec_from_file_location("taskflow_guardrail_hook", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@pytest.mark.parametrize("tool,args", [
    ("view", {"path": "docs/app-requirements.md"}),
    ("powershell", {"command": "py -m pytest -q"}),
    ("taskflowVault.search_notes", {"query": "TaskStatus"}),
])
def test_allow(tool, args):
    assert module.check({"toolName": tool, "toolArgs": args}) == {}


@pytest.mark.parametrize("tool,args", [
    ("edit", {"path": "src/taskflow/services.py", "new_string": "pass"}),
    ("edit", {"path": "pyproject.toml", "new_string": "dependency"}),
    ("powershell", {"command": "git push -u origin pr4-ontology-guardrails"}),
])
def test_warn(tool, args):
    assert module.check({"toolName": tool, "toolArgs": args})["permissionDecision"] == "ask"


@pytest.mark.parametrize("tool,args", [
    ("powershell", {"command": "git push origin main"}),
    ("powershell", {"command": "git reset --hard HEAD~1"}),
    ("create", {"path": ".env", "content": "ACCESS_TOKEN=abc"}),
    ("edit", {"path": "../taskflow-knowledge-base/Decisions/ADR-001-Local-JSON.md"}),
    ("powershell", {"command": "Set-Content ../taskflow-knowledge-base/Decisions/ADR.md hacked"}),
])
def test_block(tool, args):
    assert module.check({"toolName": tool, "toolArgs": args})["permissionDecision"] == "deny"


def test_stdout_protocol():
    event = {"toolName": "powershell", "toolArgs": {"command": "git push origin main"}}
    result = subprocess.run([sys.executable, str(SCRIPT)], input=json.dumps(event),
                            capture_output=True, text=True, check=True)
    assert json.loads(result.stdout)["permissionDecision"] == "deny"


def test_malformed_input_denied():
    result = subprocess.run([sys.executable, str(SCRIPT)], input="not-json",
                            capture_output=True, text=True, check=True)
    assert json.loads(result.stdout)["permissionDecision"] == "deny"


def test_ingest_requires_approval():
    assert module.check({"toolName": "taskflowVault.ingest_note", "toolArgs": {"title": "ADR"}})["permissionDecision"] == "ask"


def test_compatibility_payload():
    assert module.check({"tool_name": "Bash", "tool_input": {"command": "git push origin main"}})["permissionDecision"] == "deny"
