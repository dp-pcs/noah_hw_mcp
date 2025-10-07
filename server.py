"""
Homework Agent — MCP Server (Grades & Missing Assignments)

A Python MCP server that exposes tools to:
  • log in to a school portal (parent/guardian site)
  • fetch courses and current grades
  • fetch missing assignments over a time window

Uses Playwright for headless browsing to work with portals that have no public API.
Credentials are pulled from environment variables or macOS Keychain via `keyring`.
Session cookies persist to disk to avoid logging in every call.

⚠️ Replace SELECTORS and URLS with your district's portal details (Canvas, PowerSchool, Infinite Campus, Schoology, etc.).
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import List, Optional, Any

import keyring  # macOS Keychain (also works on Linux keyrings)
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from playwright.async_api import async_playwright, BrowserContext

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

# ---- Config & Helpers ----

load_dotenv()
PORTAL_BASE_URL = os.getenv("PORTAL_BASE_URL", "https://portal.example.edu")
LOGIN_URL = os.getenv("LOGIN_URL")  # Optional: specific login URL
LOGIN_PATH = os.getenv("LOGIN_PATH", "/login")
USERNAME = os.getenv("PORTAL_USERNAME") or keyring.get_password("homework-agent", "PORTAL_USERNAME")
PASSWORD = os.getenv("PORTAL_PASSWORD") or keyring.get_password("homework-agent", "PORTAL_PASSWORD")
STATE_PATH = os.getenv("STATE_PATH", "./state.json")
HEADLESS = os.getenv("HEADLESS", "true").lower() != "false"

# Use LOGIN_URL if provided, otherwise construct from PORTAL_BASE_URL + LOGIN_PATH
FULL_LOGIN_URL = LOGIN_URL if LOGIN_URL else f"{PORTAL_BASE_URL}{LOGIN_PATH}"

if not USERNAME or not PASSWORD:
    print("[WARN] Missing credentials. Set PORTAL_USERNAME/PORTAL_PASSWORD in .env or Keychain 'homework-agent'.")

async def get_context() -> BrowserContext:
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=HEADLESS)
    context = await browser.new_context(storage_state=STATE_PATH if os.path.exists(STATE_PATH) else None)
    return context

async def ensure_login(context: BrowserContext) -> None:
    page = await context.new_page()
    await page.goto(PORTAL_BASE_URL)
    # Heuristic: if we see a logout link, we're logged in already
    if await page.locator("text=Logout").count() > 0:
        await page.close()
        return
    # Otherwise perform login flow
    await page.goto(FULL_LOGIN_URL)
    # TODO: Replace selectors with your portal's fields
    await page.fill("input[name='username']", USERNAME)
    await page.fill("input[name='password']", PASSWORD)
    await page.click("button[type='submit']")
    # Wait for navigation or a known element that indicates success
    await page.wait_for_load_state("networkidle")
    # Optional: 2FA step hook here
    # Save session
    await context.storage_state(path=STATE_PATH)
    await page.close()

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

# ---- Scraping routines (replace selectors/paths) ----

async def scrape_missing_assignments(context: BrowserContext, since_days: int = 14) -> List[Assignment]:
    page = await context.new_page()
    # TODO: set to the portal's assignments URL
    await page.goto(f"{PORTAL_BASE_URL}/assignments")
    await page.wait_for_load_state("networkidle")
    items = []
    rows = page.locator(".assignment-row")  # TODO: replace
    count = await rows.count()
    cutoff = datetime.now() - timedelta(days=since_days)
    for i in range(count):
        row = rows.nth(i)
        title = await row.locator(".title").inner_text() if await row.locator(".title").count() else "Unknown"
        course = await row.locator(".course").inner_text() if await row.locator(".course").count() else "Unknown"
        status = await row.locator(".status").inner_text() if await row.locator(".status").count() else "unknown"
        due_txt = await row.locator(".due").inner_text() if await row.locator(".due").count() else None
        due_date = None
        if due_txt:
            try:
                due_date = datetime.strptime(due_txt, "%b %d, %Y")
            except:
                pass
        if status.lower().startswith("missing"):
            if not due_date or due_date >= cutoff:
                items.append(Assignment(title=title, course=course, status="missing", due_date=due_date))
    await page.close()
    return items

async def scrape_course_grades(context: BrowserContext, course_filter: Optional[str], since_days: int = 14) -> List[GradeSample]:
    page = await context.new_page()
    # TODO: set to the portal's grades/overview URL
    await page.goto(f"{PORTAL_BASE_URL}/grades")
    await page.wait_for_load_state("networkidle")
    samples: List[GradeSample] = []
    # Example: rows per course with a sparkline/history table
    courses = page.locator(".course-card")  # TODO: replace
    count = await courses.count()
    cutoff = datetime.now() - timedelta(days=since_days)
    for i in range(count):
        card = courses.nth(i)
        course = await card.locator(".course-name").inner_text() if await card.locator(".course-name").count() else "Unknown"
        if course_filter and course_filter.lower() not in course.lower():
            continue
        # Example history table selector
        rows = card.locator(".grade-history tr")
        rcount = await rows.count()
        for j in range(rcount):
            r = rows.nth(j)
            date_txt = await r.locator("td:nth-child(1)").inner_text()
            grade_txt = await r.locator("td:nth-child(2)").inner_text()
            try:
                dt = datetime.strptime(date_txt, "%b %d, %Y")
            except:
                continue
            if dt < cutoff:
                continue
            try:
                pct = float(grade_txt.replace("%", "").strip())
            except:
                pct = None
            samples.append(GradeSample(course=course, date=dt, grade_percent=pct))
    await page.close()
    return samples

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
    # Run the server using stdio transport
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
