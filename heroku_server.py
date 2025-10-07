#!/usr/bin/env python3
"""
MCP Server for Heroku deployment
"""

import json
import os
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configuration
API_KEY = "hw_agent_2024_secure_key_abc123xyz789"
PORT = int(os.environ.get("PORT", 8000))

class MCPHandler(BaseHTTPRequestHandler):
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

if __name__ == "__main__":
    print(f"🚀 Starting MCP Server on port {PORT}")
    print(f"🔑 API Key: {API_KEY}")
    
    try:
        server = HTTPServer(('0.0.0.0', PORT), MCPHandler)
        print("✅ Server started successfully!")
        server.serve_forever()
    except Exception as e:
        print(f"❌ Error: {e}")
