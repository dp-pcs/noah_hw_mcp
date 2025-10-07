#!/usr/bin/env python3
"""
Simple test server for Homework Agent MCP Server
Uses only standard library to avoid dependency issues
"""

import json
import sys
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time

# Configuration
API_KEY = "hw_agent_2024_secure_key_abc123xyz789"
HOST = "localhost"
PORT = 8000

class MCPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == "/":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                "message": "Homework Agent MCP Server (Simple Test)",
                "version": "1.0.0",
                "status": "running",
                "security": "enabled",
                "endpoints": {
                    "tools": "/tools/list",
                    "call_tool": "/tools/call",
                    "health": "/health"
                },
                "tools": [
                    "check_missing_assignments",
                    "get_course_grades", 
                    "health"
                ]
            }
            self.wfile.write(json.dumps(response, indent=2).encode())
            
        elif parsed_path.path == "/health":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                "time": datetime.now().isoformat(),
                "base_url": "https://academy20co.infinitecampus.org",
                "credentials_configured": True,
                "api_key_configured": True
            }
            self.wfile.write(json.dumps(response, indent=2).encode())
            
        elif parsed_path.path == "/tools/list":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                "tools": [
                    {
                        "name": "check_missing_assignments",
                        "description": "Return missing assignments since N days (default 14).",
                        "parameters": {
                            "since_days": {
                                "type": "integer",
                                "description": "How many days back to look.",
                                "default": 14
                            }
                        }
                    },
                    {
                        "name": "get_course_grades",
                        "description": "Return grade history for a course over the last N days.",
                        "parameters": {
                            "course": {
                                "type": "string",
                                "description": "Course name filter (e.g., 'Math')."
                            },
                            "since_days": {
                                "type": "integer",
                                "description": "Days to include (default 14).",
                                "default": 14
                            }
                        }
                    },
                    {
                        "name": "health",
                        "description": "Check server health and portal reachability.",
                        "parameters": {}
                    }
                ]
            }
            self.wfile.write(json.dumps(response, indent=2).encode())
            
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == "/tools/call":
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                request_data = json.loads(post_data.decode('utf-8'))
                tool_name = request_data.get('tool')
                arguments = request_data.get('arguments', {})
                
                # Check authentication (simplified)
                auth_header = self.headers.get('Authorization', '')
                if f'Bearer {API_KEY}' not in auth_header:
                    self.send_response(401)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Invalid API key"}).encode())
                    return
                
                # Handle tool calls
                if tool_name == "check_missing_assignments":
                    since_days = arguments.get("since_days", 14)
                    mock_assignments = [
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
                    result = {
                        "success": True,
                        "data": {
                            "count": len(mock_assignments),
                            "items": mock_assignments
                        }
                    }
                    
                elif tool_name == "get_course_grades":
                    course = arguments.get("course")
                    since_days = arguments.get("since_days", 14)
                    mock_grades = [
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
                        mock_grades = [g for g in mock_grades if course.lower() in g['course'].lower()]
                    
                    result = {
                        "success": True,
                        "data": {
                            "course_filter": course,
                            "items": mock_grades
                        }
                    }
                    
                elif tool_name == "health":
                    result = {
                        "success": True,
                        "data": {
                            "time": datetime.now().isoformat(),
                            "base_url": "https://academy20co.infinitecampus.org",
                            "credentials_configured": True,
                            "api_key_configured": True
                        }
                    }
                    
                else:
                    result = {
                        "success": False,
                        "error": f"Unknown tool: {tool_name}"
                    }
                
                # Send response
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
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Authorization, Content-Type, X-Homework-Agent')
        self.end_headers()

def start_server():
    """Start the HTTP server"""
    server = HTTPServer((HOST, PORT), MCPHandler)
    print(f"🚀 Starting Simple Homework Agent MCP Server on {HOST}:{PORT}")
    print(f"🔑 API Key: {API_KEY}")
    print(f"🌐 Server URL: http://{HOST}:{PORT}")
    print(f"🔍 Health check: http://{HOST}:{PORT}/health")
    print(f"📋 Tools list: http://{HOST}:{PORT}/tools/list")
    print(f"🔧 Test with: curl http://{HOST}:{PORT}/")
    print("=" * 50)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        server.shutdown()

if __name__ == "__main__":
    start_server()
