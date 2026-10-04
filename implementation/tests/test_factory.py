import asyncio
import importlib.util
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

    def test_generated_mcp_runs_with_official_v2_client(self):
        from mcp import Client

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            spec_path = root / "mcp.json"
            spec_path.write_text(json.dumps({
                "kind": "mcp",
                "name": "live_mcp",
                "tools": [{
                    "name": "add",
                    "description": "Add two integers",
                    "params": {"a": "int", "b": "int"},
                    "returns": "int",
                    "body": "return a + b",
                }],
            }), encoding="utf-8")
            project = root / "mcp"
            generate_mcp(root, spec_path, project)

            module_spec = importlib.util.spec_from_file_location("generated_live_mcp", project / "server.py")
            self.assertIsNotNone(module_spec)
            self.assertIsNotNone(module_spec.loader)
            module = importlib.util.module_from_spec(module_spec)
            module_spec.loader.exec_module(module)

            async def exercise():
                async with Client(module.mcp) as client:
                    tools = await client.list_tools()
                    self.assertEqual([tool.name for tool in tools.tools], ["add"])
                    result = await client.call_tool("add", {"a": 2, "b": 3})
                    self.assertFalse(result.is_error)
                    rendered = f"{result.structured_content!r} {result.content!r}"
                    self.assertIn("5", rendered)
                    self.assertEqual(client.protocol_version, "2026-07-28")

            asyncio.run(exercise())


if __name__ == "__main__":
    unittest.main()
