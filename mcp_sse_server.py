#!/usr/bin/env python3
"""
MCP Server with SSE support for testing with mcp-remote
"""

import json
import asyncio
import sys
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time

# Configuration
API_KEY = "hw_agent_2024_secure_key_abc123xyz789"
HOST = "localhost"
PORT = 8000

class MCPSSEHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/sse":
            self.send_sse_response()
        elif self.path == "/":
            self.send_json_response({
                "message": "MCP Server with SSE support",
                "version": "1.0.0",
                "status": "running",
                "endpoints": {
                    "sse": "/sse",
                    "health": "/health",
                    "tools": "/tools/list"
                }
            })
        elif self.path == "/health":
            self.send_json_response({
                "time": datetime.now().isoformat(),
                "status": "healthy",
                "api_key_configured": True
            })
        elif self.path == "/tools/list":
            self.send_json_response({
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
            })
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
    
    def send_sse_response(self):
        """Send Server-Sent Events response"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Connection', 'keep-alive')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # Send MCP initialization message
        init_message = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "mcp-remote-test",
                    "version": "1.0.0"
                }
            },
            "id": 1
        }
        
        self.wfile.write(f"data: {json.dumps(init_message)}\n\n".encode())
        self.wfile.flush()
        
        # Send tools list
        tools_message = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 2
        }
        
        self.wfile.write(f"data: {json.dumps(tools_message)}\n\n".encode())
        self.wfile.flush()
        
        # Send tools response
        tools_response = {
            "jsonrpc": "2.0",
            "result": {
                "tools": [
                    {
                        "name": "check_missing_assignments",
                        "description": "Get missing assignments from Infinite Campus",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "since_days": {
                                    "type": "integer",
                                    "description": "Number of days to look back",
                                    "default": 14
                                }
                            }
                        }
                    },
                    {
                        "name": "get_course_grades",
                        "description": "Get course grade history",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "course": {
                                    "type": "string",
                                    "description": "Course name filter"
                                },
                                "since_days": {
                                    "type": "integer",
                                    "description": "Number of days to look back",
                                    "default": 14
                                }
                            }
                        }
                    },
                    {
                        "name": "health",
                        "description": "Check server health",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    }
                ]
            },
            "id": 2
        }
        
        self.wfile.write(f"data: {json.dumps(tools_response)}\n\n".encode())
        self.wfile.flush()
    
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
    
    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Authorization, Content-Type')
        self.end_headers()

def main():
    print(f"🚀 Starting MCP SSE Server on {HOST}:{PORT}")
    print(f"🔑 API Key: {API_KEY}")
    print(f"🌐 Server URL: http://{HOST}:{PORT}")
    print(f"📡 SSE Endpoint: http://{HOST}:{PORT}/sse")
    print("=" * 50)
    
    try:
        server = HTTPServer((HOST, PORT), MCPSSEHandler)
        print("✅ Server started successfully!")
        print("🔍 Test with: curl http://localhost:8000/")
        print("📡 Test SSE with: curl http://localhost:8000/sse")
        print("🛑 Press Ctrl+C to stop")
        print("=" * 50)
        
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        server.shutdown()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
