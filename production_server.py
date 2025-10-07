#!/usr/bin/env python3
"""
Production MCP Server for Infinite Campus - For Render.com deployment
Combines HTTP API with real Infinite Campus scraping
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import List, Optional

from dotenv import load_dotenv
from playwright.async_api import async_playwright, Browser, BrowserContext

# Load environment variables
load_dotenv()

# Configuration
API_KEY = os.getenv("API_KEY", "hw_agent_2024_secure_key_abc123xyz789")
PORT = int(os.getenv("PORT", 8000))
PORTAL_BASE_URL = os.getenv("PORTAL_BASE_URL", "https://academy20co.infinitecampus.org")
LOGIN_URL = os.getenv("LOGIN_URL", "https://academy20co.infinitecampus.org/campus/SSO/academy20/portal/parents?configID=2")
USERNAME = os.getenv("PORTAL_USERNAME")
PASSWORD = os.getenv("PORTAL_PASSWORD")
HEADLESS = os.getenv("HEADLESS", "true").lower() != "false"

# Infinite Campus URLs
GRADES_URL = "https://academy20co.infinitecampus.org/campus/nav-wrapper/parent/portal/parent/grades?appName=academy20"
MISSING_ASSIGNMENTS_URL = "https://academy20co.infinitecampus.org/campus/nav-wrapper/parent/portal/parent/assignment-list?missingFilter=true&appName=academy20"

print(f"[CONFIG] Server Port: {PORT}", file=sys.stderr)
print(f"[CONFIG] Portal Base URL: {PORTAL_BASE_URL}", file=sys.stderr)
print(f"[CONFIG] Login URL: {LOGIN_URL}", file=sys.stderr)
print(f"[CONFIG] Username: {USERNAME}", file=sys.stderr)
print(f"[CONFIG] Password: {'Set' if PASSWORD else 'Not set'}", file=sys.stderr)
print(f"[CONFIG] Headless: {HEADLESS}", file=sys.stderr)
print(f"[CONFIG] API Key: {'Set' if API_KEY else 'Not set'}", file=sys.stderr)

if not USERNAME or not PASSWORD:
    print("[WARN] Missing credentials. Set PORTAL_USERNAME/PORTAL_PASSWORD in environment.", file=sys.stderr)

class InfiniteCampusScraper:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.playwright = None
        
    async def start(self):
        """Start the browser"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=HEADLESS)
        self.context = await self.browser.new_context()
        print("[BROWSER] Browser started", file=sys.stderr)
        
    async def stop(self):
        """Stop the browser"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        print("[BROWSER] Browser stopped", file=sys.stderr)
    
    async def login(self) -> bool:
        """Login to Infinite Campus"""
        try:
            print(f"[LOGIN] Navigating to {LOGIN_URL}", file=sys.stderr)
            page = await self.context.new_page()
            await page.goto(LOGIN_URL, wait_until="networkidle", timeout=30000)
            
            # Wait for Microsoft login page
            print("[LOGIN] Waiting for Microsoft login form", file=sys.stderr)
            await page.wait_for_selector('input[name="loginfmt"]', timeout=10000)
            
            # Enter username
            print(f"[LOGIN] Entering username", file=sys.stderr)
            await page.fill('input[name="loginfmt"]', USERNAME)
            await page.click('input[type="submit"]')
            
            # Wait for password field
            await page.wait_for_selector('input[name="passwd"]', timeout=10000)
            
            # Enter password
            print("[LOGIN] Entering password", file=sys.stderr)
            await page.fill('input[name="passwd"]', PASSWORD)
            await page.click('input[type="submit"]')
            
            # Wait for "Stay signed in?" prompt and click No
            try:
                await page.wait_for_selector('input[type="submit"]', timeout=5000)
                print("[LOGIN] Clicking 'No' on stay signed in prompt", file=sys.stderr)
                await page.click('input[type="submit"]')
            except:
                print("[LOGIN] No 'stay signed in' prompt", file=sys.stderr)
            
            # Wait for navigation to complete
            await page.wait_for_load_state("networkidle", timeout=30000)
            
            # Check if we're logged in
            current_url = page.url
            print(f"[LOGIN] Current URL: {current_url}", file=sys.stderr)
            
            if "portal" in current_url or "grades" in current_url:
                print("[LOGIN] ✅ Login successful!", file=sys.stderr)
                await page.close()
                return True
            else:
                print(f"[LOGIN] ❌ Login failed - unexpected URL", file=sys.stderr)
                await page.close()
                return False
                
        except Exception as e:
            print(f"[LOGIN] ❌ Login error: {e}", file=sys.stderr)
            return False
    
    async def get_missing_assignments(self, since_days: int = 14) -> List[dict]:
        """Get missing assignments"""
        try:
            print(f"[SCRAPE] Getting missing assignments", file=sys.stderr)
            page = await self.context.new_page()
            await page.goto(MISSING_ASSIGNMENTS_URL, wait_until="networkidle", timeout=30000)
            
            # Wait for content to load
            await page.wait_for_timeout(2000)
            
            # Extract assignments
            assignments = await page.evaluate('''() => {
                const assignments = [];
                const rows = document.querySelectorAll('tr');
                
                rows.forEach(row => {
                    const cells = row.querySelectorAll('td');
                    if (cells.length >= 3) {
                        const title = cells[0]?.textContent?.trim() || '';
                        const course = cells[1]?.textContent?.trim() || '';
                        const dueDate = cells[2]?.textContent?.trim() || '';
                        
                        if (title && title !== 'Assignment' && title !== 'Title' && title.length > 0) {
                            assignments.push({
                                title: title,
                                course: course,
                                due_date: dueDate,
                                status: 'missing',
                                points_possible: null
                            });
                        }
                    }
                });
                
                return assignments;
            }''')
            
            await page.close()
            print(f"[SCRAPE] Found {len(assignments)} missing assignments", file=sys.stderr)
            return assignments
            
        except Exception as e:
            print(f"[SCRAPE] Error getting missing assignments: {e}", file=sys.stderr)
            return []
    
    async def get_grades(self) -> List[dict]:
        """Get current grades"""
        try:
            print(f"[SCRAPE] Getting grades", file=sys.stderr)
            page = await self.context.new_page()
            await page.goto(GRADES_URL, wait_until="networkidle", timeout=30000)
            
            # Wait for content to load
            await page.wait_for_timeout(2000)
            
            # Extract grades
            grades = await page.evaluate('''() => {
                const grades = [];
                const rows = document.querySelectorAll('tr');
                
                rows.forEach(row => {
                    const cells = row.querySelectorAll('td');
                    if (cells.length >= 2) {
                        const course = cells[0]?.textContent?.trim() || '';
                        const grade = cells[1]?.textContent?.trim() || '';
                        
                        if (course && course !== 'Course' && course !== 'Class' && course.length > 0) {
                            // Try to extract percentage
                            const percentMatch = grade.match(/(\d+\.?\d*)%/);
                            const gradePercent = percentMatch ? parseFloat(percentMatch[1]) : null;
                            
                            grades.push({
                                course: course,
                                grade: grade,
                                grade_percent: gradePercent,
                                date: new Date().toISOString()
                            });
                        }
                    }
                });
                
                return grades;
            }''')
            
            await page.close()
            print(f"[SCRAPE] Found {len(grades)} grades", file=sys.stderr)
            return grades
            
        except Exception as e:
            print(f"[SCRAPE] Error getting grades: {e}", file=sys.stderr)
            return []

# Global scraper instance
scraper = None

async def get_scraper():
    """Get or create scraper instance"""
    global scraper
    if scraper is None:
        scraper = InfiniteCampusScraper()
        await scraper.start()
        if USERNAME and PASSWORD:
            await scraper.login()
    return scraper

class MCPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_json_response({
                "message": "Homework Agent MCP Server",
                "version": "1.0.0",
                "status": "running",
                "tools": ["check_missing_assignments", "get_course_grades", "health"],
                "endpoints": {
                    "health": "/health",
                    "tools": "/tools/list",
                    "call": "/tools/call"
                }
            })
        elif self.path == "/health":
            self.send_json_response({
                "time": datetime.now().isoformat(),
                "status": "healthy",
                "credentials_configured": bool(USERNAME and PASSWORD),
                "portal_url": PORTAL_BASE_URL
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
                        "description": "Get course grades from Infinite Campus",
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
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                if tool_name == "check_missing_assignments":
                    since_days = arguments.get("since_days", 14)
                    scraper_instance = loop.run_until_complete(get_scraper())
                    data = loop.run_until_complete(scraper_instance.get_missing_assignments(since_days))
                    result = {"success": True, "data": {"count": len(data), "items": data}}
                    
                elif tool_name == "get_course_grades":
                    course = arguments.get("course")
                    scraper_instance = loop.run_until_complete(get_scraper())
                    data = loop.run_until_complete(scraper_instance.get_grades())
                    
                    # Filter by course if specified
                    if course:
                        data = [g for g in data if course.lower() in g['course'].lower()]
                    
                    result = {"success": True, "data": {"course_filter": course, "items": data}}
                    
                elif tool_name == "health":
                    result = {
                        "success": True,
                        "data": {
                            "time": datetime.now().isoformat(),
                            "status": "healthy",
                            "credentials_configured": bool(USERNAME and PASSWORD)
                        }
                    }
                    
                else:
                    result = {"success": False, "error": f"Unknown tool: {tool_name}"}
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(result, indent=2).encode())
                
            except Exception as e:
                print(f"[API] Error: {e}", file=sys.stderr)
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

if __name__ == "__main__":
    print(f"🚀 Starting Homework Agent MCP Server on port {PORT}")
    print(f"🔑 API Key: {API_KEY}")
    print(f"🌐 Server URL: http://0.0.0.0:{PORT}")
    
    try:
        server = HTTPServer(('0.0.0.0', PORT), MCPHandler)
        print("✅ Server started successfully!")
        server.serve_forever()
    except Exception as e:
        print(f"❌ Error: {e}")
        if scraper:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(scraper.stop())
