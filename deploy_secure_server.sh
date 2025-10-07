#!/bin/bash

# Deploy secure MCP server to AWS EC2
set -e

SERVER_IP="44.220.141.9"
KEY_FILE="deployment/aws/homework-mcp-key"

echo "🚀 Deploying secure MCP server to $SERVER_IP"

# Copy files to server
echo "📁 Copying server files..."
scp -i $KEY_FILE -o StrictHostKeyChecking=no deployment/remote_server.py ubuntu@$SERVER_IP:/home/ubuntu/
scp -i $KEY_FILE -o StrictHostKeyChecking=no server.env ubuntu@$SERVER_IP:/home/ubuntu/.env
scp -i $KEY_FILE -o StrictHostKeyChecking=no deployment/requirements.txt ubuntu@$SERVER_IP:/home/ubuntu/

# SSH to server and set up
echo "🔧 Setting up server..."
ssh -i $KEY_FILE -o StrictHostKeyChecking=no ubuntu@$SERVER_IP << 'EOF'
    # Update system
    sudo apt update
    
    # Install Python and dependencies
    sudo apt install -y python3 python3-pip python3-venv git
    
    # Create virtual environment
    python3 -m venv /home/ubuntu/venv
    source /home/ubuntu/venv/bin/activate
    
    # Install Python packages
    pip install fastapi uvicorn playwright pydantic python-dotenv keyring
    
    # Install Playwright browsers
    playwright install
    
    # Set up environment
    export API_KEY="hw_agent_2024_secure_key_abc123xyz789"
    
    # Create systemd service
    sudo tee /etc/systemd/system/homework-mcp.service > /dev/null << 'SERVICE_EOF'
[Unit]
Description=Homework Agent MCP Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu
Environment=PATH=/home/ubuntu/venv/bin
Environment=API_KEY=hw_agent_2024_secure_key_abc123xyz789
ExecStart=/home/ubuntu/venv/bin/python3 remote_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE_EOF
    
    # Enable and start service
    sudo systemctl daemon-reload
    sudo systemctl enable homework-mcp
    sudo systemctl start homework-mcp
    
    # Check status
    sudo systemctl status homework-mcp --no-pager
    
    echo "✅ Server deployed and started!"
    echo "🌐 Server URL: http://$SERVER_IP:8000"
    echo "🔍 Health check: http://$SERVER_IP:8000/health"
    echo "📋 Tools list: http://$SERVER_IP:8000/tools/list"
EOF

echo "✅ Deployment complete!"
echo "🌐 Your secure MCP server is running at: http://$SERVER_IP:8000"
echo "🔑 API Key: hw_agent_2024_secure_key_abc123xyz789"
echo "📋 Use the configuration in openai_agent_config.json for your OpenAI agent"
