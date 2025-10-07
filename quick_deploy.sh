#!/bin/bash

# Quick deployment script for the new server
set -e

SERVER_IP="98.88.76.84"
KEY_FILE="deployment/aws/homework-mcp-key"

echo "🚀 Deploying to new server: $SERVER_IP"

# Wait for SSH to be ready
echo "⏳ Waiting for SSH to be ready..."
sleep 30

# Test SSH connection
echo "🔍 Testing SSH connection..."
ssh -i $KEY_FILE -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@$SERVER_IP "echo 'SSH connection successful'"

# Copy files
echo "📁 Copying server files..."
scp -i $KEY_FILE -o StrictHostKeyChecking=no deployment/remote_server.py ubuntu@$SERVER_IP:/home/ubuntu/
scp -i $KEY_FILE -o StrictHostKeyChecking=no server.env ubuntu@$SERVER_IP:/home/ubuntu/.env
scp -i $KEY_FILE -o StrictHostKeyChecking=no deployment/requirements.txt ubuntu@$SERVER_IP:/home/ubuntu/

# Setup and start server
echo "🔧 Setting up server..."
ssh -i $KEY_FILE -o StrictHostKeyChecking=no ubuntu@$SERVER_IP << 'EOF'
    # Update and install
    sudo apt update
    sudo apt install -y python3 python3-pip python3-venv
    
    # Create venv and install packages
    python3 -m venv /home/ubuntu/venv
    source /home/ubuntu/venv/bin/activate
    pip install fastapi uvicorn playwright pydantic python-dotenv keyring
    playwright install
    
    # Set environment
    export API_KEY="hw_agent_2024_secure_key_abc123xyz789"
    
    # Start server in background
    cd /home/ubuntu
    nohup python3 remote_server.py > server.log 2>&1 &
    
    echo "✅ Server started!"
    echo "🌐 Server URL: http://98.88.76.84:8000"
    echo "🔍 Health check: http://98.88.76.84:8000/health"
    echo "📋 Tools list: http://98.88.76.84:8000/tools/list"
EOF

echo "✅ Deployment complete!"
echo "🌐 Your MCP server: http://$SERVER_IP:8000"
echo "🔑 API Key: hw_agent_2024_secure_key_abc123xyz789"
