#!/usr/bin/env python3
import secrets
import string

# Generate API key
api_key = ''.join(secrets.choice(string.ascii_letters + string.digits + '_-') for _ in range(32))
print(f"API_KEY={api_key}")
