#!/bin/bash

# Start the MCP Server for Infinite Campus
# This script starts the MCP server that your AI agent can connect to

echo "🏫 Starting Homework Agent MCP Server..."
echo "Portal: Infinite Campus (Academy 20)"
echo "Username: david.proctor_p@asd20.org"
echo ""

# Check if Python is available
if ! command -v /opt/homebrew/bin/python3.12 &> /dev/null; then
    echo "❌ Python 3.12 not found at /opt/homebrew/bin/python3.12"
    echo "Please install Python 3.12 or update the path in this script"
    exit 1
fi

# Check if server file exists
if [ ! -f "improved_server.py" ]; then
    echo "❌ improved_server.py not found"
    echo "Please run this script from the MCP server directory"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found"
    echo "Make sure your credentials are configured"
fi

echo "✅ Starting MCP server..."
echo "📡 Server will listen for MCP client connections"
echo "🛑 Press Ctrl+C to stop the server"
echo ""

# Start the server
/opt/homebrew/bin/python3.12 improved_server.py
