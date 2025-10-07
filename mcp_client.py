#!/usr/bin/env python3
"""
MCP Client that communicates with the server via stdio
"""

import asyncio
import json
import subprocess
import sys

class MCPClient:
    def __init__(self, server_script="improved_server.py"):
        self.server_script = server_script
        self.process = None
        self.request_id = 0
    
    async def start_server(self):
        """Start the MCP server process"""
        self.process = subprocess.Popen(
            [sys.executable, self.server_script],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # Wait a moment for server to start
        await asyncio.sleep(2)
    
    async def call_tool(self, tool_name, arguments=None):
        """Call a tool on the MCP server"""
        if not self.process:
            await self.start_server()
        
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {}
            }
        }
        
        # Send request
        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()
        
        # Read response
        response_line = self.process.stdout.readline()
        if response_line:
            return json.loads(response_line.strip())
        else:
            return {"error": "No response received"}
    
    async def list_tools(self):
        """List available tools"""
        if not self.process:
            await self.start_server()
        
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": "tools/list",
            "params": {}
        }
        
        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()
        
        response_line = self.process.stdout.readline()
        if response_line:
            return json.loads(response_line.strip())
        else:
            return {"error": "No response received"}
    
    def stop_server(self):
        """Stop the MCP server process"""
        if self.process:
            self.process.terminate()
            self.process.wait()

async def example_mcp_client_usage():
    """Example of using the MCP client"""
    
    client = MCPClient()
    
    try:
        print("=== MCP Client Example ===\n")
        
        # List available tools
        print("1. Listing available tools...")
        tools_response = await client.list_tools()
        print("Available tools:", json.dumps(tools_response, indent=2))
        
        print("\n" + "="*50 + "\n")
        
        # Call health tool
        print("2. Calling health tool...")
        health_response = await client.call_tool("health", {})
        print("Health response:", json.dumps(health_response, indent=2))
        
        print("\n" + "="*50 + "\n")
        
        # Call missing assignments tool
        print("3. Calling missing assignments tool...")
        assignments_response = await client.call_tool("check_missing_assignments", {"since_days": 7})
        print("Assignments response:", json.dumps(assignments_response, indent=2))
        
    finally:
        client.stop_server()

if __name__ == "__main__":
    asyncio.run(example_mcp_client_usage())
