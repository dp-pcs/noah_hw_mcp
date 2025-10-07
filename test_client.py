#!/usr/bin/env python3
"""
Test client for the MCP server
"""

import asyncio
import json
import subprocess
import sys

async def test_mcp_server():
    """Test the MCP server by sending commands"""
    
    print("=== MCP Server Test Client ===")
    
    # Start the server
    print("Starting MCP server...")
    process = subprocess.Popen(
        [sys.executable, "working_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Test 1: Health check
        print("\n=== Test 1: Health Check ===")
        health_command = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "health",
                "arguments": {}
            }
        }
        
        process.stdin.write(json.dumps(health_command) + "\n")
        process.stdin.flush()
        
        # Read response
        response_line = process.stdout.readline()
        if response_line:
            response = json.loads(response_line.strip())
            print("Health response:", json.dumps(response, indent=2))
        else:
            print("No response received")
        
        # Test 2: Missing assignments
        print("\n=== Test 2: Missing Assignments ===")
        assignments_command = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "check_missing_assignments",
                "arguments": {"since_days": 7}
            }
        }
        
        process.stdin.write(json.dumps(assignments_command) + "\n")
        process.stdin.flush()
        
        response_line = process.stdout.readline()
        if response_line:
            response = json.loads(response_line.strip())
            print("Assignments response:", json.dumps(response, indent=2))
        else:
            print("No response received")
        
        # Test 3: Course grades
        print("\n=== Test 3: Course Grades ===")
        grades_command = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_course_grades",
                "arguments": {"course": "Math", "since_days": 7}
            }
        }
        
        process.stdin.write(json.dumps(grades_command) + "\n")
        process.stdin.flush()
        
        response_line = process.stdout.readline()
        if response_line:
            response = json.loads(response_line.strip())
            print("Grades response:", json.dumps(response, indent=2))
        else:
            print("No response received")
        
    except Exception as e:
        print(f"Error during testing: {e}")
    
    finally:
        # Clean up
        process.terminate()
        process.wait()
        print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_mcp_server())
