#!/usr/bin/env python3
"""
Secure Client Example for Homework Agent MCP Server
Shows how to authenticate and call tools securely
"""

import requests
import json
from typing import Dict, Any

class SecureHomeworkClient:
    def __init__(self, base_url: str, api_key: str, custom_header: str = "homework-agent-v1"):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.custom_header = custom_header
        self.session = requests.Session()
        
        # Set up authentication headers
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'X-Homework-Agent': custom_header,
            'Content-Type': 'application/json'
        })
    
    def health_check(self) -> Dict[str, Any]:
        """Check server health"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def list_tools(self) -> Dict[str, Any]:
        """List available tools"""
        response = self.session.get(f"{self.base_url}/tools/list")
        response.raise_for_status()
        return response.json()
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call a tool on the server"""
        payload = {
            "tool": tool_name,
            "arguments": arguments or {}
        }
        
        response = self.session.post(
            f"{self.base_url}/tools/call",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def get_missing_assignments(self, since_days: int = 14) -> Dict[str, Any]:
        """Get missing assignments"""
        return self.call_tool("check_missing_assignments", {"since_days": since_days})
    
    def get_course_grades(self, course: str = None, since_days: int = 14) -> Dict[str, Any]:
        """Get course grades"""
        args = {"since_days": since_days}
        if course:
            args["course"] = course
        return self.call_tool("get_course_grades", args)

def main():
    # Configuration
    SERVER_URL = "http://44.220.141.9:8000"  # Your deployed server
    API_KEY = "your_secure_api_key_here"  # Set this in your environment
    CUSTOM_HEADER = "homework-agent-v1"
    
    # Create client
    client = SecureHomeworkClient(SERVER_URL, API_KEY, CUSTOM_HEADER)
    
    try:
        # Test connection
        print("🔍 Testing server connection...")
        health = client.health_check()
        print(f"✅ Server health: {health}")
        
        # List available tools
        print("\n📋 Available tools:")
        tools = client.list_tools()
        for tool in tools['tools']:
            print(f"  - {tool['name']}: {tool['description']}")
        
        # Test tool calls
        print("\n📚 Getting missing assignments...")
        assignments = client.get_missing_assignments(since_days=7)
        print(f"Found {assignments['data']['count']} missing assignments")
        
        print("\n📊 Getting course grades...")
        grades = client.get_course_grades(since_days=7)
        print(f"Found {len(grades['data']['items'])} grade entries")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")

if __name__ == "__main__":
    main()
