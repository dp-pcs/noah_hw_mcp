#!/usr/bin/env python3
"""
Debug test to check Python environment and server loading
"""

import sys
import os

print("Python version:", sys.version)
print("Python executable:", sys.executable)
print("Current directory:", os.getcwd())

# Test basic imports
try:
    import asyncio
    print("✓ asyncio imported")
except Exception as e:
    print("✗ asyncio error:", e)

try:
    import json
    print("✓ json imported")
except Exception as e:
    print("✗ json error:", e)

try:
    from dotenv import load_dotenv
    print("✓ dotenv imported")
    load_dotenv()
    print("✓ .env loaded")
except Exception as e:
    print("✗ dotenv error:", e)

try:
    import keyring
    print("✓ keyring imported")
except Exception as e:
    print("✗ keyring error:", e)

try:
    from pydantic import BaseModel
    print("✓ pydantic imported")
except Exception as e:
    print("✗ pydantic error:", e)

try:
    from playwright.async_api import async_playwright
    print("✓ playwright imported")
except Exception as e:
    print("✗ playwright error:", e)

try:
    from mcp.server import Server
    print("✓ mcp imported")
except Exception as e:
    print("✗ mcp error:", e)

# Test environment variables
print("\nEnvironment variables:")
print("PORTAL_BASE_URL:", os.getenv("PORTAL_BASE_URL", "Not set"))
print("LOGIN_URL:", os.getenv("LOGIN_URL", "Not set"))
print("PORTAL_USERNAME:", os.getenv("PORTAL_USERNAME", "Not set"))
print("PORTAL_PASSWORD:", "Set" if os.getenv("PORTAL_PASSWORD") else "Not set")

print("\nTest completed!")
