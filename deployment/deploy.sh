#!/bin/bash

# Automated deployment script for MCP Server
# Run this on your remote server

set -e

echo "🚀 Deploying Homework Agent MCP Server..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python 3.12
echo "🐍 Installing Python 3.12..."
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev python3-pip

# Install system dependencies
echo "📚 Installing system dependencies..."
sudo apt install -y wget curl git build-essential

# Create application directory
echo "📁 Setting up application directory..."
APP_DIR="/opt/homework-mcp"
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# Copy application files
echo "📋 Copying application files..."
cp -r ../* $APP_DIR/
cd $APP_DIR

# Create virtual environment
echo "🔧 Setting up Python virtual environment..."
python3.12 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
playwright install chromium
playwright install-deps

# Create systemd service
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/homework-mcp.service > /dev/null <<EOF
[Unit]
Description=Homework Agent MCP Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
ExecStart=$APP_DIR/venv/bin/python improved_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create environment file
echo "🔐 Setting up environment configuration..."
cat > $APP_DIR/.env <<EOF
# School Portal Configuration
PORTAL_BASE_URL=https://academy20co.infinitecampus.org/campus/SSO/academy20/portal/parents?configID=2
LOGIN_URL=https://academy20co.infinitecampus.org/campus/SSO/academy20/portal/parents?configID=2
LOGIN_PATH=/login

# Credentials (CHANGE THESE!)
PORTAL_USERNAME=your_username_here
PORTAL_PASSWORD=your_password_here

# Server Configuration
STATE_PATH=./state.json
HEADLESS=true
HOST=0.0.0.0
PORT=8000
EOF

# Set permissions
echo "🔒 Setting permissions..."
chmod 600 $APP_DIR/.env
chmod +x $APP_DIR/start_server.sh

# Enable and start service
echo "🚀 Starting MCP server service..."
sudo systemctl daemon-reload
sudo systemctl enable homework-mcp
sudo systemctl start homework-mcp

# Check status
echo "📊 Checking service status..."
sudo systemctl status homework-mcp --no-pager

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit $APP_DIR/.env with your credentials"
echo "2. Restart the service: sudo systemctl restart homework-mcp"
echo "3. Check logs: sudo journalctl -u homework-mcp -f"
echo "4. Configure your AI agent to connect to this server"
echo ""
echo "🌐 Server should be running on: $(hostname -I | awk '{print $1}')"
echo "📁 Application directory: $APP_DIR"
echo "📝 Service name: homework-mcp"
