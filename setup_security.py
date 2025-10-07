#!/usr/bin/env python3
"""
Setup security for Homework Agent MCP Server
"""

import secrets
import string
import keyring
import os

def generate_api_key(length=32):
    """Generate a secure API key"""
    alphabet = string.ascii_letters + string.digits + '_-'
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def main():
    print("🔐 Setting up security for Homework Agent MCP Server")
    print("=" * 50)
    
    # Generate API key
    api_key = generate_api_key(32)
    print(f"🔑 Generated API Key: {api_key}")
    print()
    
    # Store in keyring
    try:
        keyring.set_password("homework-agent", "API_KEY", api_key)
        print("✅ API key stored in system keyring")
    except Exception as e:
        print(f"⚠️  Could not store in keyring: {e}")
        print("   You can set it manually in your .env file")
    
    print()
    print("📝 OpenAI Agent Configuration:")
    print("-" * 30)
    print(f'API_KEY={api_key}')
    print()
    
    # Update the config file
    config_file = "openai_agent_config.json"
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            content = f.read()
        
        # Replace the placeholder
        updated_content = content.replace("REPLACE_WITH_YOUR_GENERATED_KEY", api_key)
        
        with open(config_file, 'w') as f:
            f.write(updated_content)
        
        print(f"✅ Updated {config_file} with your API key")
    
    print()
    print("🌐 Server Configuration:")
    print("-" * 20)
    print(f"export API_KEY='{api_key}'")
    print()
    
    print("🔒 Security Notes:")
    print("- Keep this key secret")
    print("- Never commit to version control")
    print("- Use different keys for different environments")

if __name__ == "__main__":
    main()
