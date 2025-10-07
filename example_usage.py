#!/usr/bin/env python3
"""
Example of how to use the MCP server with your AI agent
"""

import asyncio
from improved_server import handle_call_tool

async def example_ai_agent_usage():
    """Example of how your AI agent would use the MCP server"""
    
    print("=== AI Agent Using MCP Server ===\n")
    
    # Example 1: Check for missing assignments
    print("1. Checking for missing assignments...")
    try:
        result = await handle_call_tool('check_missing_assignments', {'since_days': 7})
        assignments_data = result[0].text
        print("✅ Got missing assignments data:")
        print(assignments_data)
    except Exception as e:
        print(f"❌ Error getting assignments: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Example 2: Get course grades
    print("2. Getting Math course grades...")
    try:
        result = await handle_call_tool('get_course_grades', {'course': 'Math', 'since_days': 14})
        grades_data = result[0].text
        print("✅ Got grades data:")
        print(grades_data)
    except Exception as e:
        print(f"❌ Error getting grades: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Example 3: Health check
    print("3. Checking server health...")
    try:
        result = await handle_call_tool('health', {})
        health_data = result[0].text
        print("✅ Server health:")
        print(health_data)
    except Exception as e:
        print(f"❌ Error checking health: {e}")

if __name__ == "__main__":
    asyncio.run(example_ai_agent_usage())
