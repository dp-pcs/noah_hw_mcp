#!/usr/bin/env python3
"""
Test script to verify the MCP server is working
"""

import json
import sys
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import threading
import time

# Configuration
API_KEY = "hw_agent_2024_secure_key_abc123xyz789"
HOST = "localhost"
PORT = 8000

class TestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        print(f"GET request to: {self.path}")
        
        if self.path == "/":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                "message": "Homework Agent MCP Server (Test)",
                "version": "1.0.0",
                "status": "running",
                "tools": ["check_missing_assignments", "get_course_grades", "health"]
            }
            self.wfile.write(json.dumps(response, indent=2).encode())
            print("✅ Sent root response")
            
        elif self.path == "/health":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                "time": datetime.now().isoformat(),
                "status": "healthy"
            }
            self.wfile.write(json.dumps(response, indent=2).encode())
            print("✅ Sent health response")
            
        elif self.path == "/tools/list":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                "tools": [
                    {
                        "name": "check_missing_assignments",
                        "description": "Get missing assignments"
                    },
                    {
                        "name": "get_course_grades", 
                        "description": "Get course grades"
                    },
                    {
                        "name": "health",
                        "description": "Check server health"
                    }
                ]
            }
            self.wfile.write(json.dumps(response, indent=2).encode())
            print("✅ Sent tools list response")
            
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
            print(f"❌ 404 for {self.path}")
    
    def do_POST(self):
        """Handle POST requests"""
        print(f"POST request to: {self.path}")
        
        if self.path == "/tools/call":
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                request_data = json.loads(post_data.decode('utf-8'))
                tool_name = request_data.get('tool')
                print(f"Tool call: {tool_name}")
                
                # Mock response
                result = {
                    "success": True,
                    "data": {
                        "message": f"Mock response for {tool_name}",
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(result, indent=2).encode())
                print(f"✅ Sent tool response for {tool_name}")
                
            except Exception as e:
                print(f"❌ Error processing request: {e}")
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
            print(f"❌ 404 for {self.path}")

def start_server():
    """Start the HTTP server"""
    print(f"🚀 Starting Test MCP Server on {HOST}:{PORT}")
    print(f"🔑 API Key: {API_KEY}")
    print(f"🌐 Server URL: http://{HOST}:{PORT}")
    print("=" * 50)
    
    try:
        server = HTTPServer((HOST, PORT), TestHandler)
        print("✅ Server started successfully!")
        print("🔍 Test with: curl http://localhost:8000/")
        print("📋 Tools: curl http://localhost:8000/tools/list")
        print("🛑 Press Ctrl+C to stop")
        print("=" * 50)
        
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        server.shutdown()
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == "__main__":
    start_server()