#!/usr/bin/env python3
"""
Step-by-step test to see what happens when we run the server
"""

print("=== Step 1: Testing Configuration Loading ===")

try:
    from dotenv import load_dotenv
    import os
    load_dotenv()
    
    PORTAL_BASE_URL = os.getenv("PORTAL_BASE_URL")
    LOGIN_URL = os.getenv("LOGIN_URL") 
    USERNAME = os.getenv("PORTAL_USERNAME")
    PASSWORD = os.getenv("PORTAL_PASSWORD")
    
    print(f"✓ Portal Base URL: {PORTAL_BASE_URL}")
    print(f"✓ Login URL: {LOGIN_URL}")
    print(f"✓ Username: {USERNAME}")
    print(f"✓ Password: {'Set' if PASSWORD else 'Not set'}")
    
except Exception as e:
    print(f"✗ Configuration error: {e}")

print("\n=== Step 2: Testing Server Import ===")

try:
    from server import app, handle_list_tools, handle_call_tool
    print("✓ Server module imported successfully")
except Exception as e:
    print(f"✗ Server import error: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Step 3: Testing Tool Listing ===")

try:
    import asyncio
    async def test_tools():
        tools = await handle_list_tools()
        print(f"✓ Found {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
    
    asyncio.run(test_tools())
except Exception as e:
    print(f"✗ Tool listing error: {e}")

print("\n=== Step 4: Testing Health Tool ===")

try:
    import asyncio
    async def test_health():
        result = await handle_call_tool("health", {})
        print("✓ Health tool executed successfully")
        print("Result:", result[0].text)
    
    asyncio.run(test_health())
except Exception as e:
    print(f"✗ Health tool error: {e}")

print("\n=== Test Complete ===")
