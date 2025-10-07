#!/usr/bin/env python3
"""
Example client for connecting to remote MCP server
Use this in your OpenAI preview agent
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any, Optional

class RemoteMCPClient:
    """
    Client for connecting to remote MCP server
    """
    
    def __init__(self, server_url: str):
        self.server_url = server_url.rstrip('/')
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call a tool on the remote MCP server"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        
        url = f"{self.server_url}/tools/call"
        payload = {
            "tool": tool_name,
            "arguments": arguments or {}
        }
        
        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_missing_assignments(self, since_days: int = 14) -> Dict[str, Any]:
        """Get missing assignments"""
        return await self.call_tool("check_missing_assignments", {"since_days": since_days})
    
    async def get_course_grades(self, course: Optional[str] = None, since_days: int = 14) -> Dict[str, Any]:
        """Get course grades"""
        args = {"since_days": since_days}
        if course:
            args["course"] = course
        return await self.call_tool("get_course_grades", args)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check server health"""
        return await self.call_tool("health", {})
    
    async def list_tools(self) -> Dict[str, Any]:
        """List available tools"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        
        url = f"{self.server_url}/tools/list"
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    return {"error": f"HTTP {response.status}: {error_text}"}
        except Exception as e:
            return {"error": str(e)}

# Example usage for OpenAI preview
async def example_usage():
    """Example of how to use the remote client in your OpenAI agent"""
    
    # Replace with your server URL
    SERVER_URL = "http://your-server-ip:8000"
    
    async with RemoteMCPClient(SERVER_URL) as client:
        print("=== Remote MCP Client Example ===\n")
        
        # Health check
        print("1. Checking server health...")
        health = await client.health_check()
        print("Health:", json.dumps(health, indent=2))
        
        # Get missing assignments
        print("\n2. Getting missing assignments...")
        assignments = await client.get_missing_assignments(since_days=7)
        print("Assignments:", json.dumps(assignments, indent=2))
        
        # Get grades
        print("\n3. Getting Math grades...")
        grades = await client.get_course_grades(course="Math", since_days=14)
        print("Grades:", json.dumps(grades, indent=2))
        
        # List available tools
        print("\n4. Listing available tools...")
        tools = await client.list_tools()
        print("Tools:", json.dumps(tools, indent=2))

# Integration example for OpenAI preview
class HomeworkAgent:
    """
    Example integration for OpenAI preview agent
    """
    
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.client = None
    
    async def initialize(self):
        """Initialize the MCP client"""
        self.client = RemoteMCPClient(self.server_url)
        await self.client.__aenter__()
    
    async def cleanup(self):
        """Cleanup the MCP client"""
        if self.client:
            await self.client.__aexit__(None, None, None)
    
    async def get_homework_status(self) -> str:
        """Get a summary of homework status for the AI agent"""
        if not self.client:
            await self.initialize()
        
        try:
            # Get missing assignments
            assignments_result = await self.client.get_missing_assignments(since_days=7)
            
            if assignments_result.get("success"):
                assignments = assignments_result["data"]["items"]
                count = assignments_result["data"]["count"]
                
                if count == 0:
                    return "Great news! No missing assignments found in the last 7 days."
                else:
                    summary = f"Found {count} missing assignments:\n"
                    for assignment in assignments:
                        summary += f"- {assignment['title']} ({assignment['course']}) - Due: {assignment['due_date']}\n"
                    return summary
            else:
                return f"Error getting assignments: {assignments_result.get('error', 'Unknown error')}"
        
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def get_grade_summary(self, course: str = None) -> str:
        """Get a summary of grades for the AI agent"""
        if not self.client:
            await self.initialize()
        
        try:
            grades_result = await self.client.get_course_grades(course=course, since_days=14)
            
            if grades_result.get("success"):
                grades = grades_result["data"]["items"]
                
                if not grades:
                    return f"No recent grades found for {course or 'all courses'}."
                
                summary = f"Recent grades for {course or 'all courses'}:\n"
                for grade in grades:
                    summary += f"- {grade['course']}: {grade['grade_percent']}% (Date: {grade['date']})\n"
                return summary
            else:
                return f"Error getting grades: {grades_result.get('error', 'Unknown error')}"
        
        except Exception as e:
            return f"Error: {str(e)}"

if __name__ == "__main__":
    asyncio.run(example_usage())
