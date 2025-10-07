#!/usr/bin/env python3
"""
Generic MCP Client for any AI agent
"""

import asyncio
import json
import subprocess
import sys
from typing import Dict, Any, Optional

class HomeworkMCPClient:
    """
    Generic MCP client for the Homework Agent MCP server
    """
    
    def __init__(self, server_path: str = "/Users/davidproctor/Documents/GitHub/noah_hw_mcp/improved_server.py"):
        self.server_path = server_path
        self.process: Optional[subprocess.Popen] = None
        self.request_id = 0
    
    async def start(self):
        """Start the MCP server process"""
        if self.process:
            return
        
        self.process = subprocess.Popen(
            [sys.executable, self.server_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for server to initialize
        await asyncio.sleep(2)
        print("MCP Server started")
    
    async def stop(self):
        """Stop the MCP server process"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None
            print("MCP Server stopped")
    
    async def _send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to the MCP server"""
        if not self.process:
            await self.start()
        
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params
        }
        
        try:
            self.process.stdin.write(json.dumps(request) + "\n")
            self.process.stdin.flush()
            
            response_line = self.process.stdout.readline()
            if response_line:
                return json.loads(response_line.strip())
            else:
                return {"error": "No response received"}
        except Exception as e:
            return {"error": f"Request failed: {e}"}
    
    async def get_missing_assignments(self, since_days: int = 14) -> Dict[str, Any]:
        """Get missing assignments for the last N days"""
        return await self._send_request("tools/call", {
            "name": "check_missing_assignments",
            "arguments": {"since_days": since_days}
        })
    
    async def get_course_grades(self, course: Optional[str] = None, since_days: int = 14) -> Dict[str, Any]:
        """Get course grades for the last N days"""
        args = {"since_days": since_days}
        if course:
            args["course"] = course
        
        return await self._send_request("tools/call", {
            "name": "get_course_grades",
            "arguments": args
        })
    
    async def health_check(self) -> Dict[str, Any]:
        """Check server health"""
        return await self._send_request("tools/call", {
            "name": "health",
            "arguments": {}
        })
    
    async def list_tools(self) -> Dict[str, Any]:
        """List available tools"""
        return await self._send_request("tools/list", {})

# Example usage for AI agents
async def example_ai_agent():
    """Example of how an AI agent would use this client"""
    
    client = HomeworkMCPClient()
    
    try:
        # Start the MCP server
        await client.start()
        
        # Example 1: Check for missing assignments
        print("Checking for missing assignments...")
        assignments = await client.get_missing_assignments(since_days=7)
        print("Missing assignments:", json.dumps(assignments, indent=2))
        
        # Example 2: Get Math grades
        print("\nGetting Math grades...")
        grades = await client.get_course_grades(course="Math", since_days=14)
        print("Math grades:", json.dumps(grades, indent=2))
        
        # Example 3: Health check
        print("\nChecking server health...")
        health = await client.health_check()
        print("Server health:", json.dumps(health, indent=2))
        
    finally:
        await client.stop()

if __name__ == "__main__":
    asyncio.run(example_ai_agent())
