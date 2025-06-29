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

# Register all tools dynamically using the same factorized approach
for tool_handler in tool_handlers.values():
    tool_desc = tool_handler.get_tool_description()
    
    def create_tool_function(handler, desc):
        @app.tool(name=desc.name, description=desc.description)
        def generic_tool(**arguments) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
            try:
                logger.info(f"Tool {handler.name} called with arguments: {arguments}")
                
                # Handle the case where arguments are wrapped in an 'arguments' key
                if 'arguments' in arguments and len(arguments) == 1:
                    # Extract the actual arguments from the wrapper
                    actual_args = arguments['arguments']
                    if isinstance(actual_args, str):
                        # For simple string arguments, map to expected parameter names
                        if handler.name == "obsidian_simple_search":
                            actual_args = {"query": actual_args}
                        elif handler.name == "obsidian_list_files_in_dir":
                            actual_args = {"dirpath": actual_args}
                        elif handler.name == "obsidian_get_file_contents":
                            actual_args = {"filepath": actual_args}
                        else:
                            actual_args = {"arguments": actual_args}
                    elif isinstance(actual_args, dict):
                        pass  # Already a dict, use as-is
                    else:
                        actual_args = arguments
                else:
                    actual_args = arguments
                
                return handler.run_tool(actual_args)
            except Exception as e:
                logger.error(f"Error in tool {handler.name}: {str(e)}")
                raise RuntimeError(f"Caught Exception. Error: {str(e)}")
        return generic_tool
    
    # Register the tool
    create_tool_function(tool_handler, tool_desc)


def main():
    import sys
    import asyncio
    
    # Check for stdio mode flag
    if "--stdio" in sys.argv:
        # Run in stdio mode (for traditional MCP clients)
        asyncio.run(app.run_stdio_async())
    else:
        # Default to HTTP mode (for MCP inspector and web clients)
        import uvicorn
        streamable_app = app.streamable_http_app()
        uvicorn.run(streamable_app, host="127.0.0.1", port=9091)

if __name__ == "__main__":
    main()
