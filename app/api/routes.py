from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.models import MCPServer, SkillRecord
from app.schemas import MCPServerCreate, MCPServerOut, SkillCreate, SkillOut, SkillExecute, ToolCall
from app.security import require_api_key
from app.services.mcp_client import list_tools, call_tool
from app.services.skill_runtime import render_skill, validate_schema

router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_api_key)])

@router.get("/mcp/servers", response_model=list[MCPServerOut])
async def get_servers(db: AsyncSession = Depends(get_db)):
    return (await db.scalars(select(MCPServer).order_by(MCPServer.name))).all()

@router.post("/mcp/servers", response_model=MCPServerOut, status_code=201)
async def create_server(payload: MCPServerCreate, db: AsyncSession = Depends(get_db)):
    item = MCPServer(name=payload.name, url=str(payload.url), description=payload.description)
    db.add(item)
    try:
        await db.commit()
        await db.refresh(item)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "MCP server name already exists")
    return item

@router.get("/mcp/servers/{server_name}/tools")
async def discover_tools(server_name: str, db: AsyncSession = Depends(get_db)):
    server = await db.scalar(select(MCPServer).where(MCPServer.name == server_name, MCPServer.enabled.is_(True)))
    if not server:
        raise HTTPException(404, "MCP server not found or disabled")
    try:
        return {"server": server.name, "tools": await list_tools(server.url)}
    except TimeoutError:
        raise HTTPException(504, "MCP server request timed out")
    except Exception as exc:
        raise HTTPException(502, f"MCP server error: {type(exc).__name__}")

@router.post("/mcp/tools/call")
async def invoke_tool(payload: ToolCall, db: AsyncSession = Depends(get_db)):
    server = await db.scalar(select(MCPServer).where(MCPServer.name == payload.server, MCPServer.enabled.is_(True)))
    if not server:
        raise HTTPException(404, "MCP server not found or disabled")
    try:
        return {"server": server.name, "tool": payload.tool, "result": await call_tool(server.url, payload.tool, payload.arguments)}
    except TimeoutError:
        raise HTTPException(504, "MCP tool call timed out")
    except Exception as exc:
        raise HTTPException(502, f"MCP tool call failed: {type(exc).__name__}")

@router.get("/skills", response_model=list[SkillOut])
async def get_skills(db: AsyncSession = Depends(get_db)):
    return (await db.scalars(select(SkillRecord).where(SkillRecord.enabled.is_(True)).order_by(SkillRecord.name))).all()

@router.post("/skills", response_model=SkillOut, status_code=201)
async def create_skill(payload: SkillCreate, db: AsyncSession = Depends(get_db)):
    item = SkillRecord(name=payload.name, version=payload.version, description=payload.description, content=payload.content, input_schema=payload.input_schema)
    db.add(item)
    try:
        await db.commit()
        await db.refresh(item)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "Skill name already exists")
    return item

@router.get("/skills/{skill_name}", response_model=SkillOut)
async def get_skill(skill_name: str, db: AsyncSession = Depends(get_db)):
    item = await db.scalar(select(SkillRecord).where(SkillRecord.name == skill_name, SkillRecord.enabled.is_(True)))
    if not item:
        raise HTTPException(404, "Skill not found")
    return item

@router.post("/skills/{skill_name}/execute")
async def execute_skill(skill_name: str, payload: SkillExecute, db: AsyncSession = Depends(get_db)):
    item = await db.scalar(select(SkillRecord).where(SkillRecord.name == skill_name, SkillRecord.enabled.is_(True)))
    if not item:
        raise HTTPException(404, "Skill not found")
    try:
        validate_schema(item.input_schema or {}, payload.input)
        output = render_skill(item.content, payload.input)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    return {"skill": item.name, "version": item.version, "status": "completed", "result": {"content": output}}

@router.post("/catalog/search")
async def search_catalog(q: str = Query(min_length=1, max_length=200), db: AsyncSession = Depends(get_db)):
    term = f"%{q}%"
    skills = (await db.scalars(select(SkillRecord).where(SkillRecord.enabled.is_(True), (SkillRecord.name.ilike(term) | SkillRecord.description.ilike(term))))).all()
    servers = (await db.scalars(select(MCPServer).where(MCPServer.enabled.is_(True), (MCPServer.name.ilike(term) | MCPServer.description.ilike(term))))).all()
    return {"query": q, "skills": [{"type": "skill", "name": s.name, "version": s.version, "description": s.description} for s in skills], "mcp_servers": [{"type": "mcp_server", "name": s.name, "description": s.description} for s in servers]}
