"""MCP Client helpers — in-process calls to MCP servers via FastMCP Client."""

import json

from fastmcp import Client

from backend.mcp.supabase_server import mcp as supabase_mcp
from backend.mcp.tts_server import mcp as tts_mcp


def _extract_result(result) -> any:
    """Extract the tool return value from an MCP CallToolResult.

    FastMCP 3.x result.data can return opaque Root() objects due to
    json-schema type inference. Fall back to parsing the TextContent JSON.
    """
    if result.data is not None:
        # Verify it's not an opaque Root object
        try:
            if hasattr(result.data, '__class__') and result.data.__class__.__name__ == 'Root':
                raise ValueError("opaque Root")
            if isinstance(result.data, list) and result.data and hasattr(result.data[0], '__class__') and result.data[0].__class__.__name__ == 'Root':
                raise ValueError("opaque Root list")
            return result.data
        except (ValueError, TypeError):
            pass

    # Fall back to parsing TextContent JSON
    if result.content:
        text = result.content[0].text
        return json.loads(text)

    return None


async def call_supabase_tool(tool_name: str, arguments: dict | None = None) -> any:
    """Call a supabase-mcp tool and return the parsed result."""
    async with Client(supabase_mcp) as client:
        result = await client.call_tool(tool_name, arguments or {})
        return _extract_result(result)


async def call_tts_tool(tool_name: str, arguments: dict | None = None) -> any:
    """Call a tts-mcp tool and return the parsed result."""
    async with Client(tts_mcp) as client:
        result = await client.call_tool(tool_name, arguments or {})
        return _extract_result(result)
