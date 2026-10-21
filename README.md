# MCP & Skill Gateway MVP

Python 3.12, FastAPI, SQLAlchemy async, PostgreSQL, Redis, MCP Python SDK, Docker Compose.

## Features
- Register MCP servers and discover/call tools through the MCP Streamable HTTP transport.
- Register and execute versioned Skills stored as text templates.
- Search Skills and MCP server metadata in one catalog endpoint.
- Bearer API key authentication on `/api/v1/*` endpoints.
- OpenAPI docs, health endpoint, and basic runtime tests.

> MVP limitations: Redis is provisioned for future caching/queues but is not yet used by request handlers. Skill execution performs safe placeholder substitution only; it does not execute arbitrary code or automatically invoke MCP tools. The current schema creation is for development; use Alembic migrations before production. The bearer key is a shared development secret, not production-grade identity or tenant authorization.

## Start with Docker Compose

```bash
cp .env.example .env
# Change API_KEY in .env before exposing the service
docker compose up --build -d
docker compose logs -f api
```

Open `http://localhost:8000/docs`; health check is `http://localhost:8000/health`.

Default development token: `dev-change-me` (change it in `.env`).

## Local development

Requires Python 3.12 and reachable PostgreSQL/Redis instances.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# For local host Python, change DATABASE_URL host to localhost and SKILLS_DIR to ./skills
uvicorn app.main:app --reload
```

## API examples

Register an MCP server:

```bash
curl -X POST http://localhost:8000/api/v1/mcp/servers \\
  -H 'Authorization: Bearer dev-change-me' -H 'Content-Type: application/json' \\
  -d '{"name":"demo","url":"http://host.docker.internal:9000/mcp","description":"Demo MCP server"}'
```

Discover tools:

```bash
curl http://localhost:8000/api/v1/mcp/servers/demo/tools -H 'Authorization: Bearer dev-change-me'
```

Call a tool:

```bash
curl -X POST http://localhost:8000/api/v1/mcp/tools/call \\
  -H 'Authorization: Bearer dev-change-me' -H 'Content-Type: application/json' \\
  -d '{"server":"demo","tool":"echo","arguments":{"text":"hello"}}'
```

Execute seeded Skill:

```bash
curl -X POST http://localhost:8000/api/v1/skills/hello-skill/execute \\
  -H 'Authorization: Bearer dev-change-me' -H 'Content-Type: application/json' \\
  -d '{"input":{"name":"Ada"}}'
```

Register a Skill:

```bash
curl -X POST http://localhost:8000/api/v1/skills \\
  -H 'Authorization: Bearer dev-change-me' -H 'Content-Type: application/json' \\
  -d '{"name":"release-note","version":"1.0.0","description":"Release note template","content":"Release {{input.version}}: {{input.summary}}","input_schema":{"type":"object","required":["version","summary"],"properties":{"version":{"type":"string"},"summary":{"type":"string"}}}}'
```

Catalog search:

```bash
curl -X POST 'http://localhost:8000/api/v1/catalog/search?q=hello' -H 'Authorization: Bearer dev-change-me'
```

## Tests

```bash
pip install -r requirements.txt
pytest -q
```

`tests/test_skill_runtime.py` tests the pure Skill renderer and basic schema validation. API integration tests require a test database and should be added before production rollout.

## Security checklist before production
- Replace shared API key with OAuth 2.1/OIDC and tenant-aware RBAC/ABAC.
- Restrict outbound MCP URLs to an allowlist; block loopback, private networks, link-local, and cloud metadata endpoints to prevent SSRF.
- Add per-tool authorization, rate limits, quotas, request/response size limits, and redaction of secrets in logs.
- Add Alembic migrations, integration tests, TLS, secret manager integration, and OpenTelemetry tracing.
- Run untrusted Skill code only in isolated sandboxes; this MVP deliberately does not execute code from Skill files.
