#!/usr/bin/env python3
"""
Generate a secure API key for the Homework Agent MCP Server
"""

import secrets
import string
import keyring
import os

def generate_api_key(length: int = 32) -> str:
    """Generate a cryptographically secure API key"""
    alphabet = string.ascii_letters + string.digits + "_-"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def store_in_keyring(api_key: str):
    """Store API key in system keyring"""
    try:
        keyring.set_password("homework-agent", "API_KEY", api_key)
        print("✅ API key stored in system keyring")
    except Exception as e:
        print(f"⚠️  Could not store in keyring: {e}")
        print("   You can set it manually in your .env file")

def main():
    print("🔐 Generating secure API key for Homework Agent MCP Server")
    
    # Generate API key
    api_key = generate_api_key(32)
    print(f"\n🔑 Generated API Key: {api_key}")
    
    # Store in keyring
    store_in_keyring(api_key)
    
    # Show environment variable
    print(f"\n📝 Add this to your .env file:")
    print(f"API_KEY={api_key}")
    
    # Show keyring commands
    print(f"\n💾 Or store securely with keyring:")
    print(f"python3 -c \"import keyring; keyring.set_password('homework-agent', 'API_KEY', '{api_key}')\"")
    
    print(f"\n🔒 Security Notes:")
    print(f"  - Keep this key secret and never commit it to version control")
    print(f"  - Use different keys for different environments")
    print(f"  - Rotate keys regularly")

if __name__ == "__main__":
    main()
