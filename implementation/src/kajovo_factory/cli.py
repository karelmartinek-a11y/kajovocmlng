from __future__ import annotations

import argparse
import asyncio
import base64
import html
import json
import os
import re
import signal
import subprocess
import sys
import textwrap
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

STATE_DIR = ".kajovo"
REGISTRY_FILE = "registry.json"
RUNTIME_FILE = "runtime.json"
SECRETS_FILE = "secrets.enc"
MASTER_KEY_ENV = "KAJOVO_MASTER_KEY"
NAME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_.-]{1,63}$")
TYPE_MAP = {
    "str": "str",
    "int": "int",
    "float": "float",
    "bool": "bool",
    "dict": "dict[str, object]",
    "list[str]": "list[str]",
}


def _json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def _state(root: Path) -> Path:
    path = root / STATE_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def _registry(root: Path) -> list[dict[str, Any]]:
    return _json(_state(root) / REGISTRY_FILE, [])


def _save_registry(root: Path, rows: list[dict[str, Any]]) -> None:
    _write_json(_state(root) / REGISTRY_FILE, rows)


def _runtime(root: Path) -> dict[str, Any]:
    return _json(_state(root) / RUNTIME_FILE, {})


def _save_runtime(root: Path, rows: dict[str, Any]) -> None:
    _write_json(_state(root) / RUNTIME_FILE, rows)


def _validate_name(name: str) -> str:
    if not NAME_RE.fullmatch(name):
        raise SystemExit("name must match [A-Za-z][A-Za-z0-9_.-]{1,63}")
    return name


def _load_spec(path: Path, kind: str) -> dict[str, Any]:
    spec = _json(path, None)
    if not isinstance(spec, dict):
        raise SystemExit(f"{path}: spec must be a JSON object")
    if spec.get("kind") != kind:
        raise SystemExit(f"{path}: kind must be {kind!r}")
    spec["name"] = _validate_name(str(spec.get("name", "")))
    spec.setdefault("version", "0.1.0")
    spec.setdefault("description", "")
    spec.setdefault("secrets", [])
    if not isinstance(spec["secrets"], list) or not all(isinstance(x, str) and x for x in spec["secrets"]):
        raise SystemExit("secrets must be a list of non-empty environment variable names")
    return spec


def _param_decl(name: str, value: Any) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise SystemExit(f"invalid Python parameter name: {name}")
    if isinstance(value, str):
        type_name, required, default = value, True, None
    elif isinstance(value, dict):
        type_name = str(value.get("type", "str"))
        required = bool(value.get("required", True))
        default = value.get("default")
    else:
        raise SystemExit(f"parameter {name}: expected type string or object")
    annotation = TYPE_MAP.get(type_name)
    if not annotation:
        raise SystemExit(f"parameter {name}: unsupported type {type_name!r}; use {sorted(TYPE_MAP)}")
    if required:
        return f"{name}: {annotation}"
    return f"{name}: {annotation} | None = {default!r}"


def _tool_code(tool: dict[str, Any]) -> str:
    name = str(tool.get("name", ""))
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise SystemExit(f"invalid tool name: {name!r}")
    description = str(tool.get("description", name)).replace('"""', "'''")
    params = tool.get("params", {})
    if not isinstance(params, dict):
        raise SystemExit(f"tool {name}: params must be an object")
    decls = [_param_decl(k, v) for k, v in params.items()]
    returns = TYPE_MAP.get(str(tool.get("returns", "dict")), "dict[str, object]")
    body = tool.get("body")
    if body is None:
        pairs = ", ".join(f"{k!r}: {k}" for k in params)
        body = f"return {{'ok': True, 'inputs': {{{pairs}}}}}"
    if not isinstance(body, str) or not body.strip():
        raise SystemExit(f"tool {name}: body must be a non-empty Python statement block")
    indented = textwrap.indent(body.strip(), "        ")
    return f'''@mcp.tool()\ndef {name}({", ".join(decls)}) -> {returns}:\n    """{description}"""\n    _event("tool.start", tool={name!r})\n    try:\n{indented}\n    except Exception as exc:\n        _event("tool.error", tool={name!r}, error=type(exc).__name__)\n        raise\n'''


def _mcp_server_py(spec: dict[str, Any]) -> str:
    tools = spec.get("tools", [])
    if not isinstance(tools, list) or not tools:
        raise SystemExit("MCP spec must contain at least one tool")
    host = str(spec.get("host", "127.0.0.1"))
    port = int(spec.get("port", 8000))
    path = str(spec.get("path", "/mcp"))
    tool_blocks = "\n\n".join(_tool_code(t) for t in tools)
    return f'''from __future__ import annotations\n\nimport json\nimport os\nimport sys\nimport time\n\nfrom mcp.server.mcpserver import MCPServer\nfrom starlette.requests import Request\nfrom starlette.responses import JSONResponse\n\nNAME = {spec["name"]!r}\nVERSION = {spec["version"]!r}\nHOST = os.getenv("KAJOVO_HOST", {host!r})\nPORT = int(os.getenv("KAJOVO_PORT", {port!r}))\nMCP_PATH = os.getenv("KAJOVO_MCP_PATH", {path!r})\n\nmcp = MCPServer(NAME)\n\ndef _event(event: str, **fields: object) -> None:\n    record = {{"ts": time.time(), "component": NAME, "version": VERSION, "event": event, **fields}}\n    print(json.dumps(record, ensure_ascii=False, separators=(",", ":")), file=sys.stderr, flush=True)\n\n@mcp.custom_route("/health", methods=["GET"])\nasync def health(_: Request) -> JSONResponse:\n    return JSONResponse({{"status": "ok", "component": NAME, "version": VERSION}})\n\n{tool_blocks}\n\nif __name__ == "__main__":\n    _event("server.start", host=HOST, port=PORT, path=MCP_PATH)\n    mcp.run(\n        transport="streamable-http",\n        host=HOST,\n        port=PORT,\n        streamable_http_path=MCP_PATH,\n        stateless_http=True,\n        json_response=True,\n    )\n'''


def _mcp_manifest(spec: dict[str, Any]) -> dict[str, Any]:
    host = str(spec.get("host", "127.0.0.1"))
    port = int(spec.get("port", 8000))
    path = str(spec.get("path", "/mcp"))
    return {
        "schemaVersion": 1,
        "kind": "MCP_SERVER",
        "name": spec["name"],
        "version": spec["version"],
        "description": spec.get("description", ""),
        "entrypoint": "server.py",
        "transport": "streamable-http",
        "protocolTarget": "2026-07-28",
        "endpoint": f"http://{host}:{port}{path}",
        "health": f"http://{host}:{port}/health",
        "secrets": [{"name": x, "required": True, "source": "environment"} for x in spec["secrets"]],
        "monitoring": {"logFormat": "json-lines", "liveness": "/health"},
    }


def _agent_py(spec: dict[str, Any]) -> str:
    instructions = str(spec.get("instructions", "You are a helpful assistant."))
    model = spec.get("model")
    servers = spec.get("mcpServers", [])
    if not isinstance(servers, list):
        raise SystemExit("mcpServers must be a list")
    normalized = []
    for idx, row in enumerate(servers):
        if isinstance(row, str):
            normalized.append({"name": f"mcp-{idx+1}", "url": row})
        elif isinstance(row, dict) and row.get("url"):
            normalized.append(dict(row))
        else:
            raise SystemExit("each mcpServers item must be a URL string or object with url")
    model_line = f", model={str(model)!r}" if model else ""
    return f'''from __future__ import annotations\n\nimport asyncio\nimport contextlib\nimport os\nimport sys\n\nfrom agents import Agent, Runner\nfrom agents.mcp import MCPServerStreamableHttp\n\nNAME = {spec["name"]!r}\nINSTRUCTIONS = {instructions!r}\nMCP_SERVERS = {normalized!r}\n\nasync def run_once(user_input: str) -> str:\n    async with contextlib.AsyncExitStack() as stack:\n        active = []\n        for item in MCP_SERVERS:\n            headers = dict(item.get("headers", {{}}))\n            token_env = item.get("token_env")\n            if token_env:\n                token = os.environ[token_env]\n                headers.setdefault("Authorization", f"Bearer {{token}}")\n            server = MCPServerStreamableHttp(\n                name=item.get("name", item["url"]),\n                params={{"url": item["url"], "headers": headers, "timeout": item.get("timeout", 15)}},\n                cache_tools_list=True,\n                max_retry_attempts=int(item.get("max_retry_attempts", 2)),\n            )\n            active.append(await stack.enter_async_context(server))\n        agent = Agent(name=NAME, instructions=INSTRUCTIONS, mcp_servers=active{model_line})\n        result = await Runner.run(agent, user_input)\n        return str(result.final_output)\n\nasync def _main() -> None:\n    prompt = " ".join(sys.argv[1:]).strip() or input("Prompt: ")\n    print(await run_once(prompt))\n\nif __name__ == "__main__":\n    asyncio.run(_main())\n'''


def _agent_manifest(spec: dict[str, Any]) -> dict[str, Any]:
    secrets = list(spec["secrets"])
    if "OPENAI_API_KEY" not in secrets:
        secrets.append("OPENAI_API_KEY")
    for row in spec.get("mcpServers", []):
        if isinstance(row, dict) and row.get("token_env") and row["token_env"] not in secrets:
            secrets.append(row["token_env"])
    return {
        "schemaVersion": 1,
        "kind": "OPENAI_AGENT",
        "name": spec["name"],
        "version": spec["version"],
        "description": spec.get("description", ""),
        "entrypoint": "agent.py",
        "model": spec.get("model"),
        "mcpServers": spec.get("mcpServers", []),
        "secrets": [{"name": x, "required": True, "source": "environment"} for x in secrets],
    }


def _component_readme(manifest: dict[str, Any]) -> str:
    if manifest["kind"] == "MCP_SERVER":
        run = "python server.py"
        test = f"curl {manifest['health']}"
    else:
        run = 'python agent.py "Hello"'
        test = "Set OPENAI_API_KEY before running."
    return f"""# {manifest['name']}\n\nGenerated by `kajovo-factory`.\n\n## Run\n\n```bash\npip install -e .\n{run}\n```\n\n## Check\n\n```bash\n{test}\n```\n\nSecrets are declared in `kajovo.manifest.json` and are read from the environment.\n"""


def _project_pyproject(kind: str, name: str) -> str:
    dep = '"mcp>=2,<3"' if kind == "MCP_SERVER" else '"openai-agents>=0.7,<1", "mcp>=2,<3"'
    return f'''[build-system]\nrequires = ["setuptools>=75", "wheel"]\nbuild-backend = "setuptools.build_meta"\n\n[project]\nname = {name.replace("_", "-")!r}\nversion = "0.1.0"\nrequires-python = ">=3.11"\ndependencies = [{dep}]\n'''


def _register(root: Path, project: Path, manifest: dict[str, Any]) -> None:
    rows = _registry(root)
    item = {
        "name": manifest["name"],
        "kind": manifest["kind"],
        "version": manifest["version"],
        "path": str(project.resolve()),
        "endpoint": manifest.get("endpoint"),
        "health": manifest.get("health"),
        "secrets": [x["name"] for x in manifest.get("secrets", [])],
    }
    rows = [r for r in rows if r.get("name") != item["name"]]
    rows.append(item)
    rows.sort(key=lambda r: r["name"])
    _save_registry(root, rows)


def generate_mcp(root: Path, spec_path: Path, out: Path) -> None:
    spec = _load_spec(spec_path, "mcp")
    out.mkdir(parents=True, exist_ok=True)
    manifest = _mcp_manifest(spec)
    (out / "server.py").write_text(_mcp_server_py(spec), encoding="utf-8")
    (out / "pyproject.toml").write_text(_project_pyproject("MCP_SERVER", spec["name"]), encoding="utf-8")
    _write_json(out / "kajovo.manifest.json", manifest)
    (out / ".env.example").write_text("".join(f"{x}=\n" for x in spec["secrets"]), encoding="utf-8")
    (out / "README.md").write_text(_component_readme(manifest), encoding="utf-8")
    _register(root, out, manifest)
    print(out.resolve())


def generate_agent(root: Path, spec_path: Path, out: Path) -> None:
    spec = _load_spec(spec_path, "agent")
    out.mkdir(parents=True, exist_ok=True)
    manifest = _agent_manifest(spec)
    (out / "agent.py").write_text(_agent_py(spec), encoding="utf-8")
    (out / "pyproject.toml").write_text(_project_pyproject("OPENAI_AGENT", spec["name"]), encoding="utf-8")
    _write_json(out / "kajovo.manifest.json", manifest)
    (out / ".env.example").write_text("".join(f"{x['name']}=\n" for x in manifest["secrets"]), encoding="utf-8")
    (out / "README.md").write_text(_component_readme(manifest), encoding="utf-8")
    _register(root, out, manifest)
    print(out.resolve())


def _fernet():
    try:
        from cryptography.fernet import Fernet
    except ImportError as exc:
        raise SystemExit("install kajovo-factory[secrets] or kajovo-factory[all]") from exc
    key = os.getenv(MASTER_KEY_ENV)
    if not key:
        raise SystemExit(f"{MASTER_KEY_ENV} is not set; run `kajovo-factory secret-init` and store the printed key outside this repository")
    try:
        return Fernet(key.encode("ascii"))
    except Exception as exc:
        raise SystemExit(f"invalid {MASTER_KEY_ENV}") from exc


def secret_init() -> None:
    try:
        from cryptography.fernet import Fernet
    except ImportError as exc:
        raise SystemExit("install kajovo-factory[secrets] or kajovo-factory[all]") from exc
    print(Fernet.generate_key().decode("ascii"))


def _load_secrets(root: Path) -> dict[str, str]:
    path = _state(root) / SECRETS_FILE
    if not path.exists():
        return {}
    raw = _fernet().decrypt(path.read_bytes())
    return json.loads(raw.decode("utf-8"))


def _save_secrets(root: Path, data: dict[str, str]) -> None:
    path = _state(root) / SECRETS_FILE
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    path.write_bytes(_fernet().encrypt(payload))


def secret_set(root: Path, name: str, value: str) -> None:
    data = _load_secrets(root)
    data[name] = value
    _save_secrets(root, data)
    print(name)


def secret_list(root: Path) -> None:
    for name in sorted(_load_secrets(root)):
        print(name)


def secret_delete(root: Path, name: str) -> None:
    data = _load_secrets(root)
    data.pop(name, None)
    _save_secrets(root, data)


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _component(root: Path, name: str) -> dict[str, Any]:
    for item in _registry(root):
        if item.get("name") == name:
            return item
    raise SystemExit(f"unknown component: {name}")


def run_component(root: Path, name: str) -> None:
    item = _component(root, name)
    if item["kind"] != "MCP_SERVER":
        raise SystemExit("background run is currently for MCP_SERVER; use `agent` for agents")
    runtime = _runtime(root)
    old = runtime.get(name)
    if old and _pid_alive(int(old.get("pid", 0))):
        raise SystemExit(f"{name} already running as PID {old['pid']}")
    project = Path(item["path"])
    env = dict(os.environ)
    try:
        stored = _load_secrets(root)
    except SystemExit:
        stored = {}
    for secret in item.get("secrets", []):
        if secret not in env and secret in stored:
            env[secret] = stored[secret]
        if secret not in env:
            raise SystemExit(f"missing required secret: {secret}")
    logs = _state(root) / "logs"
    logs.mkdir(exist_ok=True)
    log_path = logs / f"{name}.log"
    log_handle = log_path.open("ab", buffering=0)
    kwargs: dict[str, Any] = {"cwd": project, "env": env, "stdout": log_handle, "stderr": log_handle}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
    else:
        kwargs["start_new_session"] = True
    proc = subprocess.Popen([sys.executable, "server.py"], **kwargs)
    runtime[name] = {"pid": proc.pid, "startedAt": time.time(), "log": str(log_path.resolve())}
    _save_runtime(root, runtime)
    print(proc.pid)


def stop_component(root: Path, name: str) -> None:
    runtime = _runtime(root)
    item = runtime.get(name)
    if not item:
        return
    pid = int(item.get("pid", 0))
    if _pid_alive(pid):
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            try:
                os.killpg(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
    runtime.pop(name, None)
    _save_runtime(root, runtime)


def status_rows(root: Path) -> list[dict[str, Any]]:
    runtime = _runtime(root)
    rows = []
    dirty = False
    for item in _registry(root):
        r = dict(item)
        current = runtime.get(item["name"])
        if current and _pid_alive(int(current.get("pid", 0))):
            r["status"] = "RUNNING"
            r["pid"] = current["pid"]
            r["log"] = current.get("log")
        else:
            r["status"] = "STOPPED"
            if current:
                runtime.pop(item["name"], None)
                dirty = True
        rows.append(r)
    if dirty:
        _save_runtime(root, runtime)
    return rows


def print_status(root: Path) -> None:
    rows = status_rows(root)
    if not rows:
        print("No registered components.")
        return
    width = max(len(r["name"]) for r in rows)
    for r in rows:
        print(f"{r['name']:<{width}}  {r['kind']:<12}  {r['status']:<7}  {r.get('endpoint') or ''}")


def run_agent(root: Path, name: str, prompt: str) -> None:
    item = _component(root, name)
    if item["kind"] != "OPENAI_AGENT":
        raise SystemExit("component is not an OPENAI_AGENT")
    env = dict(os.environ)
    try:
        stored = _load_secrets(root)
    except SystemExit:
        stored = {}
    for secret in item.get("secrets", []):
        if secret not in env and secret in stored:
            env[secret] = stored[secret]
        if secret not in env:
            raise SystemExit(f"missing required secret: {secret}")
    subprocess.run([sys.executable, "agent.py", prompt], cwd=Path(item["path"]), env=env, check=True)


class DashboardHandler(BaseHTTPRequestHandler):
    root: Path

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/api/state":
            payload = json.dumps(status_rows(self.root), ensure_ascii=False).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        body = """<!doctype html><html><head><meta charset='utf-8'><title>KájovoCML Factory</title>
<style>body{font-family:system-ui;margin:32px;background:#111;color:#eee}table{border-collapse:collapse;width:100%}td,th{padding:10px;border-bottom:1px solid #333;text-align:left}.RUNNING{color:#8f8}.STOPPED{color:#f99}code{color:#9cf}</style></head><body>
<h1>KájovoCML Factory</h1><p>Local registry, runtime state, endpoints and declared secrets.</p><table><thead><tr><th>Name</th><th>Kind</th><th>Status</th><th>Endpoint</th><th>Secrets</th></tr></thead><tbody id='rows'></tbody></table>
<script>async function load(){const rows=await (await fetch('/api/state')).json();document.getElementById('rows').innerHTML=rows.map(r=>`<tr><td>${esc(r.name)}</td><td>${esc(r.kind)}</td><td class="${esc(r.status)}">${esc(r.status)}</td><td><code>${esc(r.endpoint||'')}</code></td><td>${esc((r.secrets||[]).join(', '))}</td></tr>`).join('')}function esc(v){return String(v).replace(/[&<>\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}load();setInterval(load,3000)</script></body></html>""".encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: object) -> None:
        return


def serve_ui(root: Path, host: str, port: int) -> None:
    handler = type("BoundDashboardHandler", (DashboardHandler,), {"root": root})
    server = ThreadingHTTPServer((host, port), handler)
    print(f"http://{host}:{port}")
    server.serve_forever()


def doctor(root: Path) -> int:
    problems = []
    if sys.version_info < (3, 11):
        problems.append("Python 3.11+ required")
    names = [r.get("name") for r in _registry(root)]
    if len(names) != len(set(names)):
        problems.append("duplicate registry names")
    for item in _registry(root):
        project = Path(item["path"])
        manifest = project / "kajovo.manifest.json"
        if not manifest.exists():
            problems.append(f"{item['name']}: missing kajovo.manifest.json")
        entry = project / ("server.py" if item["kind"] == "MCP_SERVER" else "agent.py")
        if not entry.exists():
            problems.append(f"{item['name']}: missing entrypoint")
    if problems:
        for problem in problems:
            print("FAIL", problem)
        return 1
    print("OK")
    return 0


def selftest(root: Path) -> int:
    tmp = root / ".kajovo-selftest"
    if tmp.exists():
        import shutil
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    mcp_spec = tmp / "mcp.json"
    agent_spec = tmp / "agent.json"
    _write_json(mcp_spec, {
        "kind": "mcp", "name": "demo_mcp", "tools": [
            {"name": "add", "description": "Add two integers", "params": {"a": "int", "b": "int"}, "returns": "int", "body": "return a + b"}
        ]
    })
    _write_json(agent_spec, {"kind": "agent", "name": "demo_agent", "instructions": "Answer briefly."})
    generate_mcp(tmp, mcp_spec, tmp / "generated-mcp")
    generate_agent(tmp, agent_spec, tmp / "generated-agent")
    import py_compile
    py_compile.compile(str(tmp / "generated-mcp/server.py"), doraise=True)
    py_compile.compile(str(tmp / "generated-agent/agent.py"), doraise=True)
    assert _json(tmp / "generated-mcp/kajovo.manifest.json", {})["protocolTarget"] == "2026-07-28"
    assert len(_registry(tmp)) == 2
    print("SELFTEST OK")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="kajovo-factory")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="workspace containing .kajovo state")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("new-mcp"); p.add_argument("spec", type=Path); p.add_argument("--out", type=Path, required=True)
    p = sub.add_parser("new-agent"); p.add_argument("spec", type=Path); p.add_argument("--out", type=Path, required=True)
    sub.add_parser("list")
    p = sub.add_parser("run"); p.add_argument("name")
    p = sub.add_parser("stop"); p.add_argument("name")
    p = sub.add_parser("agent"); p.add_argument("name"); p.add_argument("prompt")
    sub.add_parser("secret-init")
    p = sub.add_parser("secret-set"); p.add_argument("name"); p.add_argument("value", nargs="?")
    sub.add_parser("secret-list")
    p = sub.add_parser("secret-delete"); p.add_argument("name")
    p = sub.add_parser("ui"); p.add_argument("--host", default="127.0.0.1"); p.add_argument("--port", type=int, default=8765)
    sub.add_parser("doctor")
    sub.add_parser("selftest")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    if args.command == "new-mcp":
        generate_mcp(root, args.spec.resolve(), args.out.resolve()); return 0
    if args.command == "new-agent":
        generate_agent(root, args.spec.resolve(), args.out.resolve()); return 0
    if args.command == "list": print_status(root); return 0
    if args.command == "run": run_component(root, args.name); return 0
    if args.command == "stop": stop_component(root, args.name); return 0
    if args.command == "agent": run_agent(root, args.name, args.prompt); return 0
    if args.command == "secret-init": secret_init(); return 0
    if args.command == "secret-set":
        value = args.value if args.value is not None else input("Secret value: ")
        secret_set(root, args.name, value); return 0
    if args.command == "secret-list": secret_list(root); return 0
    if args.command == "secret-delete": secret_delete(root, args.name); return 0
    if args.command == "ui": serve_ui(root, args.host, args.port); return 0
    if args.command == "doctor": return doctor(root)
    if args.command == "selftest": return selftest(root)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
