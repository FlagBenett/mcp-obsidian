import json
import logging
from collections.abc import Sequence
from functools import lru_cache
from typing import Any
import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

load_dotenv()

from . import tools

# Load environment variables

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-obsidian")

api_key = os.getenv("OBSIDIAN_API_KEY")
if not api_key:
    raise ValueError(f"OBSIDIAN_API_KEY environment variable required. Working directory: {os.getcwd()}")

app = FastMCP("mcp-obsidian")

tool_handlers = {}
def add_tool_handler(tool_class: tools.ToolHandler):
    global tool_handlers

    tool_handlers[tool_class.name] = tool_class

def get_tool_handler(name: str) -> tools.ToolHandler | None:
    if name not in tool_handlers:
        return None
    
    return tool_handlers[name]

add_tool_handler(tools.ListFilesInDirToolHandler())
add_tool_handler(tools.ListFilesInVaultToolHandler())
add_tool_handler(tools.GetFileContentsToolHandler())
add_tool_handler(tools.SearchToolHandler())
add_tool_handler(tools.PatchContentToolHandler())
add_tool_handler(tools.AppendContentToolHandler())
add_tool_handler(tools.PutContentToolHandler())
add_tool_handler(tools.DeleteFileToolHandler())
add_tool_handler(tools.ComplexSearchToolHandler())
add_tool_handler(tools.BatchGetFileContentsToolHandler())
add_tool_handler(tools.PeriodicNotesToolHandler())
add_tool_handler(tools.RecentPeriodicNotesToolHandler())
add_tool_handler(tools.RecentChangesToolHandler())

# Register each tool individually with proper function signatures
def register_search_tool():
    @app.tool(name="obsidian_simple_search", description="Search for text in the vault.")
    def search_tool(arguments: str, context_length: int = 100) -> list[TextContent]:
        # Handle both direct string and nested arguments format
        if isinstance(arguments, str):
            query = arguments
        else:
            query = arguments.get("query", arguments) if isinstance(arguments, dict) else str(arguments)
        
        handler = get_tool_handler("obsidian_simple_search")
        result = handler.run_tool({"query": query, "context_length": context_length})
        return result

def register_list_vault_tool():
    @app.tool(name="obsidian_list_files_in_vault", description="Lists all files and directories in the root directory of your Obsidian vault.")
    def list_vault_tool() -> list[TextContent]:
        handler = get_tool_handler("obsidian_list_files_in_vault")
        result = handler.run_tool({})
        return result

def register_list_dir_tool():
    @app.tool(name="obsidian_list_files_in_dir", description="Lists all files and directories that exist in a specific Obsidian directory.")
    def list_dir_tool(dirpath: str) -> list[TextContent]:
        handler = get_tool_handler("obsidian_list_files_in_dir")
        result = handler.run_tool({"dirpath": dirpath})
        return result

def register_get_file_tool():
    @app.tool(name="obsidian_get_file_contents", description="Read the content of a file in your Obsidian vault.")
    def get_file_tool(filepath: str) -> list[TextContent]:
        handler = get_tool_handler("obsidian_get_file_contents")
        result = handler.run_tool({"filepath": filepath})
        return result

# Register additional tools
def register_recent_changes_tool():
    @app.tool(name="obsidian_get_recent_changes", description="Get recently changed files in the vault.")
    def recent_changes_tool(num_files: int = 10) -> list[TextContent]:
        handler = get_tool_handler("obsidian_get_recent_changes")
        result = handler.run_tool({"num_files": num_files})
        return result

def register_append_content_tool():
    @app.tool(name="obsidian_append_content", description="Append content to a file.")
    def append_content_tool(filepath: str, content: str) -> list[TextContent]:
        handler = get_tool_handler("obsidian_append_content")
        result = handler.run_tool({"filepath": filepath, "content": content})
        return result

def register_put_content_tool():
    @app.tool(name="obsidian_put_content", description="Write content to a file.")
    def put_content_tool(filepath: str, content: str) -> list[TextContent]:
        handler = get_tool_handler("obsidian_put_content")
        result = handler.run_tool({"filepath": filepath, "content": content})
        return result

def register_delete_file_tool():
    @app.tool(name="obsidian_delete_file", description="Delete a file from the vault.")
    def delete_file_tool(filepath: str) -> list[TextContent]:
        handler = get_tool_handler("obsidian_delete_file")
        result = handler.run_tool({"filepath": filepath})
        return result

def register_complex_search_tool():
    @app.tool(name="obsidian_complex_search", description="Perform a complex search in the vault.")
    def complex_search_tool(query: str) -> list[TextContent]:
        handler = get_tool_handler("obsidian_complex_search")
        result = handler.run_tool({"query": query})
        return result

# Register all tools
register_search_tool()
register_list_vault_tool()
register_list_dir_tool()
register_get_file_tool()
register_recent_changes_tool()
register_append_content_tool()
register_put_content_tool()
register_delete_file_tool()
register_complex_search_tool()


def main():
    import uvicorn
    streamable_app = app.streamable_http_app()
    uvicorn.run(streamable_app, host="127.0.0.1", port=9091)

if __name__ == "__main__":
    main()
