#!/usr/bin/env python3
"""
Minimal test that will definitely work
"""

import os
from dotenv import load_dotenv

# Test 1: Basic Python
print("=== Minimal Test ===")
print("Python is working!")

# Test 2: Load environment
load_dotenv()
print("Environment loaded!")

# Test 3: Check configuration
PORTAL_BASE_URL = os.getenv("PORTAL_BASE_URL")
LOGIN_URL = os.getenv("LOGIN_URL")
USERNAME = os.getenv("PORTAL_USERNAME")
PASSWORD = os.getenv("PORTAL_PASSWORD")

print(f"Portal URL: {PORTAL_BASE_URL}")
print(f"Login URL: {LOGIN_URL}")
print(f"Username: {USERNAME}")
print(f"Password: {'Set' if PASSWORD else 'Not set'}")

# Test 4: Try importing playwright
try:
    from playwright.async_api import async_playwright
    print("✓ Playwright imported successfully")
except Exception as e:
    print(f"✗ Playwright import failed: {e}")

# Test 5: Try importing MCP
try:
    from mcp.server import Server
    print("✓ MCP imported successfully")
except Exception as e:
    print(f"✗ MCP import failed: {e}")

print("=== Test Complete ===")

# Write to file as backup
with open("minimal_test_results.txt", "w") as f:
    f.write("Minimal test completed successfully\n")
    f.write(f"Portal URL: {PORTAL_BASE_URL}\n")
    f.write(f"Login URL: {LOGIN_URL}\n")
    f.write(f"Username: {USERNAME}\n")
    f.write(f"Password: {'Set' if PASSWORD else 'Not set'}\n")

print("Results also written to minimal_test_results.txt")
