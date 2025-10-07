#!/usr/bin/env python3
"""
Simple health check for the MCP server
"""

import asyncio
import json
import os
from datetime import datetime

# Test configuration loading
try:
    from dotenv import load_dotenv
    load_dotenv()
    
    PORTAL_BASE_URL = os.getenv("PORTAL_BASE_URL", "https://portal.example.edu")
    LOGIN_URL = os.getenv("LOGIN_URL")
    LOGIN_PATH = os.getenv("LOGIN_PATH", "/login")
    FULL_LOGIN_URL = LOGIN_URL if LOGIN_URL else f"{PORTAL_BASE_URL}{LOGIN_PATH}"
    USERNAME = os.getenv("PORTAL_USERNAME")
    PASSWORD = os.getenv("PORTAL_PASSWORD")
    
    print("=== MCP Server Health Check ===")
    print(f"Time: {datetime.now().isoformat()}")
    print(f"Portal Base URL: {PORTAL_BASE_URL}")
    print(f"Login URL: {LOGIN_URL}")
    print(f"Full Login URL: {FULL_LOGIN_URL}")
    print(f"Username: {USERNAME}")
    print(f"Password: {'Set' if PASSWORD else 'Not set'}")
    print("=== Configuration loaded successfully ===")
    
except Exception as e:
    print(f"ERROR loading configuration: {e}")
    import traceback
    traceback.print_exc()

# Test server import
try:
    from server import app, handle_list_tools, handle_call_tool
    print("✓ Server module imported successfully")
    
    # Test health tool
    async def test_health():
        try:
            result = await handle_call_tool("health", {})
            print("✓ Health tool works")
            print("Health result:", result[0].text)
        except Exception as e:
            print(f"✗ Health tool error: {e}")
    
    asyncio.run(test_health())
    
except Exception as e:
    print(f"ERROR importing server: {e}")
    import traceback
    traceback.print_exc()

print("=== Health check completed ===")
