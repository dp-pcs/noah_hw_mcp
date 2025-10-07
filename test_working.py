#!/usr/bin/env python3
"""
Test that will definitely work and show output
"""

import sys
import os

# Write to file immediately
with open("test_output.txt", "w") as f:
    f.write("=== Python Test Started ===\n")
    f.write("Python is working!\n")
    
    # Test imports
    try:
        from dotenv import load_dotenv
        f.write("✓ dotenv imported\n")
        
        load_dotenv()
        f.write("✓ .env loaded\n")
        
        PORTAL_BASE_URL = os.getenv("PORTAL_BASE_URL")
        LOGIN_URL = os.getenv("LOGIN_URL")
        USERNAME = os.getenv("PORTAL_USERNAME")
        PASSWORD = os.getenv("PORTAL_PASSWORD")
        
        f.write(f"Portal URL: {PORTAL_BASE_URL}\n")
        f.write(f"Login URL: {LOGIN_URL}\n")
        f.write(f"Username: {USERNAME}\n")
        f.write(f"Password: {'Set' if PASSWORD else 'Not set'}\n")
        
    except Exception as e:
        f.write(f"✗ Error: {e}\n")
    
    # Test playwright
    try:
        from playwright.async_api import async_playwright
        f.write("✓ playwright imported\n")
    except Exception as e:
        f.write(f"✗ playwright error: {e}\n")
    
    # Test MCP
    try:
        from mcp.server import Server
        f.write("✓ MCP imported\n")
    except Exception as e:
        f.write(f"✗ MCP error: {e}\n")
    
    f.write("=== Test Complete ===\n")

# Also try to print to stdout
print("Test completed - check test_output.txt")
sys.stdout.flush()
