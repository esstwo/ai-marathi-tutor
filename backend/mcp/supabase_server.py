"""Supabase MCP Server — registers all DB tools via FastMCP.

Auth functions (signup_user, login_user, refresh_session) are excluded
because they return complex Supabase auth response objects that don't
serialize to MCP's JSON format.
"""

from fastmcp import FastMCP

from backend.mcp import supabase_tools

mcp = FastMCP(name="supabase-mcp")

# Child operations
mcp.tool()(supabase_tools.get_child_profile)
mcp.tool()(supabase_tools.get_children_by_parent)
mcp.tool()(supabase_tools.create_child)
mcp.tool()(supabase_tools.update_child_stats)
mcp.tool()(supabase_tools.verify_child_belongs_to_parent)

# Parent record (not auth — just DB insert)
mcp.tool()(supabase_tools.create_parent_record)

# Lesson operations
mcp.tool()(supabase_tools.list_lessons)
mcp.tool()(supabase_tools.get_lesson_by_id)
mcp.tool()(supabase_tools.get_lesson_context)
mcp.tool()(supabase_tools.record_lesson_completion)

# Conversation operations
mcp.tool()(supabase_tools.start_conversation_record)
mcp.tool()(supabase_tools.save_message)
mcp.tool()(supabase_tools.get_conversation_messages)
mcp.tool()(supabase_tools.get_conversation)
mcp.tool()(supabase_tools.update_conversation_message_count)
mcp.tool()(supabase_tools.end_conversation_record)

# Progress query operations
mcp.tool()(supabase_tools.count_completed_lessons)
mcp.tool()(supabase_tools.count_conversations)
mcp.tool()(supabase_tools.get_conversations_with_ratios)
