# Kájovo Factory — usable MVP

This directory is the first runnable implementation layer next to the SSOT. It does not replace or weaken the SSOT. It provides a practical control plane and generators for simple MCP servers and OpenAI Agents SDK agents.

## Install

```bash
cd implementation
python -m venv .venv
# activate the venv
pip install -e ".[all]"
```

## Generate an MCP server

```bash
kajovo-factory --root .. new-mcp examples/mcp-calculator.json --out ../generated/calculator_mcp
kajovo-factory --root .. run calculator_mcp
kajovo-factory --root .. list
```

The generated server uses the official MCP Python SDK v2, Streamable HTTP, the 2026-07-28 protocol line, a `/health` route, JSON-line operational events and a machine-readable `kajovo.manifest.json`.

## Generate an OpenAI Agents SDK agent

```bash
kajovo-factory --root .. new-agent examples/agent.json --out ../generated/factory_agent
export OPENAI_API_KEY=...
kajovo-factory --root .. agent factory_agent "Use the calculator to add 2 and 3"
```

## Secrets

The local secret store is encrypted with Fernet. The master key is never stored in the repository.

```bash
kajovo-factory secret-init
export KAJOVO_MASTER_KEY='the printed key'
kajovo-factory --root .. secret-set OPENAI_API_KEY
kajovo-factory --root .. secret-list
```

## Local dashboard

```bash
kajovo-factory --root .. ui
```

Open `http://127.0.0.1:8765`. It shows registered components, runtime state, endpoints and secret names (never secret values).

## Validation

```bash
kajovo-factory selftest
python -m unittest discover -s tests -v
```
