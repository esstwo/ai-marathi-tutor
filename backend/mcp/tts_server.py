"""TTS MCP Server — text-to-speech tool via FastMCP."""

from fastmcp import FastMCP

from backend.mcp.tts_tools import speak_marathi

mcp = FastMCP(name="tts-mcp")
mcp.tool()(speak_marathi)
