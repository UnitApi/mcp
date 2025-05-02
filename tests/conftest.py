import sys
import types

# Create a fake mcp.server.fastmcp module
fastmcp = types.ModuleType('mcp.server.fastmcp')
fastmcp.FastMCP = object  # Dummy class
fastmcp.Context = object  # Dummy class

# Create a fake mcp.server package
server = types.ModuleType('mcp.server')
server.fastmcp = fastmcp

# Create a fake mcp package
mcp = types.ModuleType('mcp')
mcp.server = server

# Insert into sys.modules
sys.modules['mcp'] = mcp
sys.modules['mcp.server'] = server
sys.modules['mcp.server.fastmcp'] = fastmcp
