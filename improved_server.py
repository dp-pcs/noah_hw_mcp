#!/usr/bin/env python3
"""
Improved MCP Server for Infinite Campus with Microsoft Authentication
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from typing import List, Optional, Any

import keyring
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from playwright.async_api import async_playwright, BrowserContext, Page

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)

# ---- Configuration ----
load_dotenv()
PORTAL_BASE_URL = os.getenv("PORTAL_BASE_URL", "https://portal.example.edu")
LOGIN_URL = os.getenv("LOGIN_URL")
LOGIN_PATH = os.getenv("LOGIN_PATH", "/login")
USERNAME = os.getenv("PORTAL_USERNAME") or keyring.get_password("homework-agent", "PORTAL_USERNAME")
PASSWORD = os.getenv("PORTAL_PASSWORD") or keyring.get_password("homework-agent", "PORTAL_PASSWORD")
STATE_PATH = os.getenv("STATE_PATH", "./state.json")
HEADLESS = os.getenv("HEADLESS", "true").lower() != "false"

# Use LOGIN_URL if provided, otherwise construct from PORTAL_BASE_URL + LOGIN_PATH
FULL_LOGIN_URL = LOGIN_URL if LOGIN_URL else f"{PORTAL_BASE_URL}{LOGIN_PATH}"

# Log configuration
print(f"[CONFIG] Portal Base URL: {PORTAL_BASE_URL}", file=sys.stderr)
print(f"[CONFIG] Login URL: {FULL_LOGIN_URL}", file=sys.stderr)
print(f"[CONFIG] Username: {USERNAME}", file=sys.stderr)
print(f"[CONFIG] Password: {'Set' if PASSWORD else 'Not set'}", file=sys.stderr)
print(f"[CONFIG] Headless: {HEADLESS}", file=sys.stderr)

if not USERNAME or not PASSWORD:
    print("[WARN] Missing credentials. Set PORTAL_USERNAME/PORTAL_PASSWORD in .env or Keychain 'homework-agent'.", file=sys.stderr)

# ---- Data Models ----
class Assignment(BaseModel):
    title: str
    course: str
    due_date: Optional[datetime] = None
    status: str = Field(description="missing | submitted | graded | excused | unknown")
    points_possible: Optional[float] = None
    points_earned: Optional[float] = None
    link: Optional[str] = None

class GradeSample(BaseModel):
    course: str
    date: datetime
    grade_percent: Optional[float]

# ---- Browser Functions ----
async def get_context() -> BrowserContext:
    print("[BROWSER] Starting browser...", file=sys.stderr)
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(
        headless=HEADLESS, 
        slow_mo=1000,
        args=['--disable-web-security', '--disable-features=VizDisplayCompositor']
    )
    context = await browser.new_context(
        storage_state=STATE_PATH if os.path.exists(STATE_PATH) else None,
        viewport={'width': 1280, 'height': 720}
    )
    return context

async def wait_for_page_load(page: Page, timeout: int = 10000):
    """Wait for page to load with better error handling"""
    try:
        await page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception as e:
        print(f"[PAGE] Network idle timeout, continuing...", file=sys.stderr)
        # Continue anyway, page might still be usable

async def ensure_login(context: BrowserContext) -> None:
    print("[LOGIN] Starting login process...", file=sys.stderr)
    page = await context.new_page()
    
    try:
        # Go to main portal first
        print(f"[LOGIN] Going to portal: {PORTAL_BASE_URL}", file=sys.stderr)
        await page.goto(PORTAL_BASE_URL)
        await wait_for_page_load(page)
        
        # Check if already logged in by looking for Infinite Campus specific elements
        logged_in_indicators = [
            "text=Logout",
            "text=Sign Out", 
            "text=Welcome",
            "text=Dashboard",
            "[data-testid='logout']",
            ".logout-button",
            "a[href*='logout']"
        ]
        
        logged_in = False
        for indicator in logged_in_indicators:
            try:
                if await page.locator(indicator).count() > 0:
                    print(f"[LOGIN] Already logged in (found: {indicator})", file=sys.stderr)
                    logged_in = True
                    break
            except:
                continue
        
        if logged_in:
            await page.close()
            return
        
        # Take screenshot of current state
        await page.screenshot(path="login_attempt_1.png")
        print("[LOGIN] Screenshot saved as login_attempt_1.png", file=sys.stderr)
        
        # Look for Microsoft login elements
        print("[LOGIN] Looking for Microsoft login form...", file=sys.stderr)
        
        # Microsoft login selectors
        username_selectors = [
            "input[name='loginfmt']",
            "input[name='username']", 
            "input[type='email']",
            "input[placeholder*='email']",
            "input[placeholder*='user']",
            "#i0116",
            "#userNameInput"
        ]
        
        password_selectors = [
            "input[name='passwd']",
            "input[name='password']",
            "input[type='password']",
            "#i0118",
            "#passwordInput"
        ]
        
        submit_selectors = [
            "input[type='submit']",
            "input[value='Sign in']",
            "input[value='Next']",
            "button[type='submit']",
            "#idSIButton9",
            ".win-button"
        ]
        
        # Find and fill username
        username_filled = False
        for selector in username_selectors:
            try:
                if await page.locator(selector).count() > 0:
                    print(f"[LOGIN] Filling username with selector: {selector}", file=sys.stderr)
                    await page.fill(selector, USERNAME)
                    username_filled = True
                    break
            except:
                continue
        
        if not username_filled:
            print("[LOGIN] ERROR: Could not find username field", file=sys.stderr)
            await page.screenshot(path="login_error_username.png")
            await page.close()
            return
        
        # Find and click next/submit for username
        next_clicked = False
        for selector in submit_selectors:
            try:
                if await page.locator(selector).count() > 0:
                    print(f"[LOGIN] Clicking next with selector: {selector}", file=sys.stderr)
                    await page.click(selector)
                    next_clicked = True
                    break
            except:
                continue
        
        if not next_clicked:
            print("[LOGIN] WARNING: Could not find next button, trying Enter key", file=sys.stderr)
            await page.keyboard.press("Enter")
        
        # Wait for password page
        print("[LOGIN] Waiting for password page...", file=sys.stderr)
        await wait_for_page_load(page, 5000)
        
        # Take screenshot of password page
        await page.screenshot(path="login_attempt_2.png")
        print("[LOGIN] Screenshot saved as login_attempt_2.png", file=sys.stderr)
        
        # Find and fill password
        password_filled = False
        for selector in password_selectors:
            try:
                if await page.locator(selector).count() > 0:
                    print(f"[LOGIN] Filling password with selector: {selector}", file=sys.stderr)
                    await page.fill(selector, PASSWORD)
                    password_filled = True
                    break
            except:
                continue
        
        if not password_filled:
            print("[LOGIN] ERROR: Could not find password field", file=sys.stderr)
            await page.screenshot(path="login_error_password.png")
            await page.close()
            return
        
        # Find and click sign in
        signin_clicked = False
        for selector in submit_selectors:
            try:
                if await page.locator(selector).count() > 0:
                    print(f"[LOGIN] Clicking sign in with selector: {selector}", file=sys.stderr)
                    await page.click(selector)
                    signin_clicked = True
                    break
            except:
                continue
        
        if not signin_clicked:
            print("[LOGIN] WARNING: Could not find sign in button, trying Enter key", file=sys.stderr)
            await page.keyboard.press("Enter")
        
        # Wait for login to complete
        print("[LOGIN] Waiting for login to complete...", file=sys.stderr)
        await wait_for_page_load(page, 15000)
        
        # Take screenshot after login
        await page.screenshot(path="login_attempt_3.png")
        print("[LOGIN] Screenshot saved as login_attempt_3.png", file=sys.stderr)
        
        print(f"[LOGIN] After login, URL: {page.url}", file=sys.stderr)
        
        # Check for success indicators
        success_indicators = [
            "text=Logout",
            "text=Sign Out",
            "text=Welcome", 
            "text=Dashboard",
            "text=Grades",
            "text=Assignments",
            "[data-testid='logout']",
            ".logout-button"
        ]
        
        login_successful = False
        for indicator in success_indicators:
            try:
                if await page.locator(indicator).count() > 0:
                    print(f"[LOGIN] Login successful! Found: {indicator}", file=sys.stderr)
                    login_successful = True
                    break
            except:
                continue
        
        if not login_successful:
            print("[LOGIN] WARNING: Login may have failed - no clear success indicators found", file=sys.stderr)
            print("[LOGIN] Check the screenshots to see what happened", file=sys.stderr)
        
        # Save session
        await context.storage_state(path=STATE_PATH)
        print("[LOGIN] Session saved", file=sys.stderr)
        
    except Exception as e:
        print(f"[LOGIN] ERROR: {e}", file=sys.stderr)
        import traceback
        print(traceback.format_exc(), file=sys.stderr)
        await page.screenshot(path="login_error.png")
    finally:
        await page.close()

# ---- Scraping Functions ----
async def scrape_missing_assignments(context: BrowserContext, since_days: int = 14) -> List[Assignment]:
    print(f"[SCRAPE] Getting missing assignments (last {since_days} days)", file=sys.stderr)
    page = await context.new_page()
    
    try:
        # Go to assignments page
        assignments_url = f"{PORTAL_BASE_URL}/assignments"
        print(f"[SCRAPE] Going to: {assignments_url}", file=sys.stderr)
        await page.goto(assignments_url)
        await wait_for_page_load(page)
        
        # Take screenshot
        await page.screenshot(path="assignments_page.png")
        print("[SCRAPE] Screenshot saved as assignments_page.png", file=sys.stderr)
        
        # For now, return mock data since we need to customize selectors
        print("[SCRAPE] Returning mock data (selectors need customization)", file=sys.stderr)
        return [
            Assignment(
                title="Sample Assignment 1",
                course="Math",
                status="missing",
                due_date=datetime.now() + timedelta(days=2)
            ),
            Assignment(
                title="Sample Assignment 2", 
                course="Science",
                status="missing",
                due_date=datetime.now() + timedelta(days=5)
            )
        ]
        
    except Exception as e:
        print(f"[SCRAPE] ERROR: {e}", file=sys.stderr)
        return []
    finally:
        await page.close()

async def scrape_course_grades(context: BrowserContext, course_filter: Optional[str], since_days: int = 14) -> List[GradeSample]:
    print(f"[SCRAPE] Getting course grades (last {since_days} days)", file=sys.stderr)
    page = await context.new_page()
    
    try:
        # Go to grades page
        grades_url = f"{PORTAL_BASE_URL}/grades"
        print(f"[SCRAPE] Going to: {grades_url}", file=sys.stderr)
        await page.goto(grades_url)
        await wait_for_page_load(page)
        
        # Take screenshot
        await page.screenshot(path="grades_page.png")
        print("[SCRAPE] Screenshot saved as grades_page.png", file=sys.stderr)
        
        # For now, return mock data since we need to customize selectors
        print("[SCRAPE] Returning mock data (selectors need customization)", file=sys.stderr)
        return [
            GradeSample(
                course="Math",
                date=datetime.now() - timedelta(days=1),
                grade_percent=85.5
            ),
            GradeSample(
                course="Science",
                date=datetime.now() - timedelta(days=3),
                grade_percent=92.0
            )
        ]
        
    except Exception as e:
        print(f"[SCRAPE] ERROR: {e}", file=sys.stderr)
        return []
    finally:
        await page.close()

# ---- MCP Server Setup ----
app = Server("homework-agent")

@app.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools."""
    return [
        Tool(
            name="check_missing_assignments",
            description="Return missing assignments since N days (default 14).",
            inputSchema={
                "type": "object",
                "properties": {
                    "since_days": {
                        "type": "integer",
                        "description": "How many days back to look.",
                        "default": 14
                    }
                }
            }
        ),
        Tool(
            name="get_course_grades",
            description="Return grade history for a course over the last N days.",
            inputSchema={
                "type": "object",
                "properties": {
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
            }
        ),
        Tool(
            name="health",
            description="Check server health and portal reachability.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[TextContent]:
    """Handle tool calls."""
    
    print(f"[TOOL] Called tool: {name} with args: {arguments}", file=sys.stderr)
    
    if name == "check_missing_assignments":
        since_days = arguments.get("since_days", 14)
        context = await get_context()
        try:
            await ensure_login(context)
            data = await scrape_missing_assignments(context, since_days=since_days)
            result = {
                "count": len(data),
                "items": [item.model_dump() for item in data]
            }
            return [TextContent(type="text", text=json.dumps(result, default=str, indent=2))]
        finally:
            await context.close()
    
    elif name == "get_course_grades":
        course = arguments.get("course")
        since_days = arguments.get("since_days", 14)
        context = await get_context()
        try:
            await ensure_login(context)
            data = await scrape_course_grades(context, course_filter=course, since_days=since_days)
            result = {
                "course_filter": course,
                "items": [item.model_dump() for item in data]
            }
            return [TextContent(type="text", text=json.dumps(result, default=str, indent=2))]
        finally:
            await context.close()
    
    elif name == "health":
        result = {
            "time": datetime.now().isoformat(),
            "base_url": PORTAL_BASE_URL,
            "login_url": FULL_LOGIN_URL,
            "state_file": os.path.abspath(STATE_PATH),
            "credentials_configured": bool(USERNAME and PASSWORD)
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    print("[SERVER] Starting MCP server...", file=sys.stderr)
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="homework-agent",
                server_version="1.0.0",
                capabilities=app.get_capabilities(
                    notification_options=None,
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
