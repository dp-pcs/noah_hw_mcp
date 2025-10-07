#!/usr/bin/env python3
"""
Test configuration loading
"""

import os
from dotenv import load_dotenv

def test_config():
    load_dotenv()
    
    PORTAL_BASE_URL = os.getenv("PORTAL_BASE_URL", "https://portal.example.edu")
    LOGIN_URL = os.getenv("LOGIN_URL")
    LOGIN_PATH = os.getenv("LOGIN_PATH", "/login")
    FULL_LOGIN_URL = LOGIN_URL if LOGIN_URL else f"{PORTAL_BASE_URL}{LOGIN_PATH}"
    
    print("Configuration Test Results:")
    print(f"Portal Base URL: {PORTAL_BASE_URL}")
    print(f"Login URL: {LOGIN_URL}")
    print(f"Login Path: {LOGIN_PATH}")
    print(f"Full Login URL: {FULL_LOGIN_URL}")
    print(f"Username: {os.getenv('PORTAL_USERNAME', 'Not set')}")
    print(f"Password: {'Set' if os.getenv('PORTAL_PASSWORD') else 'Not set'}")

if __name__ == "__main__":
    test_config()
