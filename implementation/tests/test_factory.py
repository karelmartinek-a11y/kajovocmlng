import json
import tempfile
import unittest
from pathlib import Path

from kajovo_factory.cli import generate_agent, generate_mcp, doctor


class FactoryTests(unittest.TestCase):
    def test_generates_mcp_and_agent(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            mcp_spec = root / "mcp.json"
            mcp_spec.write_text(json.dumps({
                "kind": "mcp",
                "name": "test_mcp",
                "tools": [{"name": "echo", "params": {"text": "str"}, "returns": "str", "body": "return text"}],
            }), encoding="utf-8")
            agent_spec = root / "agent.json"
            agent_spec.write_text(json.dumps({
                "kind": "agent", "name": "test_agent", "instructions": "Test"
            }), encoding="utf-8")
            generate_mcp(root, mcp_spec, root / "mcp")
            generate_agent(root, agent_spec, root / "agent")
            manifest = json.loads((root / "mcp/kajovo.manifest.json").read_text())
            self.assertEqual(manifest["protocolTarget"], "2026-07-28")
            self.assertEqual(manifest["transport"], "streamable-http")
            self.assertEqual(doctor(root), 0)


if __name__ == "__main__":
    unittest.main()
