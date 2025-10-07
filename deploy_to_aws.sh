#!/bin/bash

# Deploy MCP server to AWS EC2
set -e

SERVER_IP="98.88.76.84"
KEY_FILE="deployment/aws/homework-mcp-key"

echo "🚀 Deploying MCP server to AWS EC2: $SERVER_IP"

# Create a simple server file for AWS
cat > aws_server.py << 'EOF'
#!/usr/bin/env python3
"""
MCP Server for AWS deployment
"""

import json
import sys
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
import os

# Configuration
API_KEY = "hw_agent_2024_secure_key_abc123xyz789"
HOST = "0.0.0.0"  # Listen on all interfaces
PORT = 8000

class MCPHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {format % args}")
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        if self.path == "/":
            response = {
                "message": "Homework Agent MCP Server",
                "version": "1.0.0",
                "status": "running",
                "tools": ["check_missing_assignments", "get_course_grades", "health"]
            }
        elif self.path == "/health":
            response = {
                "time": datetime.now().isoformat(),
                "status": "healthy",
                "api_key_configured": True
            }
        elif self.path == "/tools/list":
            response = {
                "tools": [
                    {
                        "name": "check_missing_assignments",
                        "description": "Get missing assignments from Infinite Campus",
                        "parameters": {
                            "since_days": {"type": "integer", "default": 14}
                        }
                    },
                    {
                        "name": "get_course_grades",
                        "description": "Get course grade history",
                        "parameters": {
                            "course": {"type": "string"},
                            "since_days": {"type": "integer", "default": 14}
                        }
                    },
                    {
                        "name": "health",
                        "description": "Check server health",
                        "parameters": {}
                    }
                ]
            }
        else:
            response = {"error": "Not found"}
            self.send_response(404)
        
        self.wfile.write(json.dumps(response, indent=2).encode())
    
    def do_POST(self):
        if self.path == "/tools/call":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                request_data = json.loads(post_data.decode('utf-8'))
                tool_name = request_data.get('tool')
                arguments = request_data.get('arguments', {})
                
                # Check API key
                auth_header = self.headers.get('Authorization', '')
                if f'Bearer {API_KEY}' not in auth_header:
                    self.send_response(401)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Invalid API key"}).encode())
                    return
                
                # Handle tools
                if tool_name == "check_missing_assignments":
                    since_days = arguments.get("since_days", 14)
                    mock_data = [
                        {
                            "title": "Math Worksheet - Chapter 5",
                            "course": "Pre-Algebra",
                            "status": "missing",
                            "due_date": (datetime.now() + timedelta(days=2)).isoformat(),
                            "points_possible": 100.0
                        },
                        {
                            "title": "Science Lab Report",
                            "course": "Science",
                            "status": "missing",
                            "due_date": (datetime.now() + timedelta(days=5)).isoformat(),
                            "points_possible": 50.0
                        }
                    ]
                    result = {"success": True, "data": {"count": len(mock_data), "items": mock_data}}
                    
                elif tool_name == "get_course_grades":
                    course = arguments.get("course")
                    mock_data = [
                        {
                            "course": "Pre-Algebra",
                            "date": (datetime.now() - timedelta(days=1)).isoformat(),
                            "grade_percent": 85.5
                        },
                        {
                            "course": "Science",
                            "date": (datetime.now() - timedelta(days=3)).isoformat(),
                            "grade_percent": 92.0
                        }
                    ]
                    if course:
                        mock_data = [g for g in mock_data if course.lower() in g['course'].lower()]
                    result = {"success": True, "data": {"course_filter": course, "items": mock_data}}
                    
                elif tool_name == "health":
                    result = {"success": True, "data": {"time": datetime.now().isoformat(), "status": "healthy"}}
                    
                else:
                    result = {"success": False, "error": f"Unknown tool: {tool_name}"}
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(result, indent=2).encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Authorization, Content-Type')
        self.end_headers()

def main():
    print(f"🚀 Starting MCP Server on {HOST}:{PORT}")
    print(f"🔑 API Key: {API_KEY}")
    print(f"🌐 Public URL: http://{SERVER_IP}:{PORT}")
    
    try:
        server = HTTPServer((HOST, PORT), MCPHandler)
        print("✅ Server started successfully!")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        server.shutdown()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
EOF

echo "📁 Created server file"

# Try to copy files to server (if SSH works)
echo "📤 Attempting to copy files to server..."
if scp -i $KEY_FILE -o StrictHostKeyChecking=no -o ConnectTimeout=10 aws_server.py ubuntu@$SERVER_IP:/home/ubuntu/ 2>/dev/null; then
    echo "✅ Files copied successfully"
    
    # Try to start server on remote machine
    echo "🚀 Starting server on remote machine..."
    ssh -i $KEY_FILE -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@$SERVER_IP << 'EOF'
        cd /home/ubuntu
        python3 aws_server.py &
        echo "✅ Server started in background"
        sleep 2
        echo "🔍 Testing server..."
        curl -s http://localhost:8000/ | head -3
EOF
else
    echo "❌ SSH connection failed"
    echo "📋 Manual deployment instructions:"
    echo "1. SSH to server: ssh -i $KEY_FILE ubuntu@$SERVER_IP"
    echo "2. Copy the aws_server.py content to the server"
    echo "3. Run: python3 aws_server.py"
fi

echo "🌐 Your MCP server should be available at: http://$SERVER_IP:8000"
echo "🔑 API Key: $API_KEY"
echo "📋 Test with: curl http://$SERVER_IP:8000/"
