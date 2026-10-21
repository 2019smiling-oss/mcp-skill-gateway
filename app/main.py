from contextlib import asynccontextmanager
from pathlib import Path
import yaml
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import select
from app.core.config import settings
from app.core.db import Base, SessionLocal, engine
from app.models import SkillRecord
from app.api.routes import router

async def seed_skills() -> None:
    root = Path(settings.skills_dir)
    if not root.exists():
        return
    async with SessionLocal() as db:
        for file in root.glob("*/SKILL.md"):
            content = file.read_text(encoding="utf-8")
            name = file.parent.name
            existing = await db.scalar(select(SkillRecord).where(SkillRecord.name == name))
            if existing:
                continue
            manifest_file = file.parent / "manifest.yaml"
            manifest = yaml.safe_load(manifest_file.read_text(encoding="utf-8")) if manifest_file.exists() else {}
            db.add(SkillRecord(name=manifest.get("name", name), version=str(manifest.get("version", "1.0.0")), description=manifest.get("description", ""), content=content, input_schema=manifest.get("input_schema_inline", {})))
        await db.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_skills()
    yield
    await engine.dispose()

app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.include_router(router)

@app.get("/health")
async def health():
    return {"status": "ok", "service": settings.app_name}

@app.get("/")
async def root():
    return JSONResponse({"service": settings.app_name, "docs": "/docs", "health": "/health"})
