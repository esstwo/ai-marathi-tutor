"""MCP Client helpers — in-process calls to MCP servers via FastMCP Client."""

from fastmcp import Client

from backend.mcp.supabase_server import mcp as supabase_mcp
from backend.mcp.tts_server import mcp as tts_mcp


async def call_supabase_tool(tool_name: str, arguments: dict | None = None) -> any:
    """Call a supabase-mcp tool and return the parsed result."""
    async with Client(supabase_mcp) as client:
        result = await client.call_tool(tool_name, arguments or {})
        return result.data


async def call_tts_tool(tool_name: str, arguments: dict | None = None) -> any:
    """Call a tts-mcp tool and return the parsed result."""
    async with Client(tts_mcp) as client:
        result = await client.call_tool(tool_name, arguments or {})
        return result.data
