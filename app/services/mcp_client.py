import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from app.core.config import settings

async def list_tools(url: str) -> list[dict]:
    async with asyncio.timeout(settings.request_timeout_seconds):
        async with streamablehttp_client(url) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.list_tools()
                return [
                    {
                        "name": tool.name,
                        "description": tool.description or "",
                        "input_schema": tool.inputSchema,
                    }
                    for tool in result.tools
                ]

async def call_tool(url: str, tool_name: str, arguments: dict) -> dict:
    async with asyncio.timeout(settings.request_timeout_seconds):
        async with streamablehttp_client(url) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                return {
                    "is_error": bool(result.isError),
                    "content": [
                        ({"type": item.type, "text": item.text} if getattr(item, "type", None) == "text" else {"type": getattr(item, "type", "unknown")})
                        for item in result.content
                    ],
                    "structured_content": getattr(result, "structuredContent", None),
                }
