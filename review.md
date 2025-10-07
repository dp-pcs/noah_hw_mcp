"""
Homework Agent — MCP Server Starter (Grades & Missing Assignments)

What this is
------------
A minimal Python MCP server that exposes tools your agent can call to:
  • log in to a school portal (parent/guardian site)
  • fetch courses and current grades
  • fetch missing assignments over a time window

It uses Playwright for headless browsing so it works even if the portal has no public API.
Credentials are pulled from environment variables or your macOS Keychain via `keyring`.
Session cookies persist to disk to avoid logging in every call.

⚠️ Replace SELECTORS and URLS with your district's portal details (Canvas, PowerSchool, Infinite Campus, Schoology, etc.).

Quick start
-----------
1) python -m venv .venv && source .venv/bin/activate
2) pip install playwright mcp keyring pydantic python-dotenv
3) playwright install
4) Copy .env.example to .env and fill values (or use Keychain)
5) Run the server: python server.py
6) Connect from your Agent tool config to this MCP server (stdio or tcp) per your agent host's docs.

Security notes
--------------
• Prefer macOS Keychain (or 1Password Connect) over raw .env.
• Session cookies are stored at ./state.json — keep this file private.
• Honor the school portal Terms of Use; throttle requests.

"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import List, Optional

import keyring  # macOS Keychain (also works on Linux keyrings)
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from playwright.async_api import async_playwright, BrowserContext

# ---- Minimal MCP plumbing (generic) ----
# This is a lightweight shim so you can register tools without pulling in a large framework.
# If you're already using your own MCP scaffolding, replace this with your framework's Tool/Server registration.

class ToolParam(BaseModel):
    name: str
    type: str
    description: str
    required: bool = False
    enum: Optional[List[str]] = None

class ToolSpec(BaseModel):
    name: str
    description: str
    parameters: List[ToolParam]

class MCPServer:
    def __init__(self):
        self.tools = {}

    def tool(self, spec: ToolSpec):
        def decorator(fn):
            self.tools[spec.name] = {"spec": spec, "fn": fn}
            return fn
        return decorator

    async def handle(self, request_json: str) -> str:
        """Very small stdio-style handler. Expecting {"tool":"name","args":{...}}."""
        req = json.loads(request_json)
        tool = self.tools.get(req.get("tool"))
        if not tool:
            return json.dumps({"error": f"Unknown tool {req.get('tool')}"})
        result = await tool["fn"](**req.get("args", {}))
        return json.dumps({"ok": True, "data": result}, default=str)

server = MCPServer()

# ---- Config & Helpers ----

load_dotenv()
PORTAL_BASE_URL = os.getenv("PORTAL_BASE_URL", "https://portal.example.edu")
LOGIN_PATH = os.getenv("LOGIN_PATH", "/login")
USERNAME = os.getenv("PORTAL_USERNAME") or keyring.get_password("homework-agent", "PORTAL_USERNAME")
PASSWORD = os.getenv("PORTAL_PASSWORD") or keyring.get_password("homework-agent", "PORTAL_PASSWORD")
STATE_PATH = os.getenv("STATE_PATH", "./state.json")
HEADLESS = os.getenv("HEADLESS", "true").lower() != "false"

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
    await page.goto(PORTAL_BASE_URL + LOGIN_PATH)
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
                items.append(Assignment(title=title, course=course, status="missing", due_date=due_date).dict())
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
            samples.append(GradeSample(course=course, date=dt, grade_percent=pct).dict())
    await page.close()
    return samples

# ---- Tools exposed to the Agent ----

@server.tool(ToolSpec(
    name="check_missing_assignments",
    description="Return missing assignments since N days (default 14).",
    parameters=[
        ToolParam(name="since_days", type="integer", description="How many days back to look.", required=False),
    ],
))
async def check_missing_assignments(since_days: int = 14):
    context = await get_context()
    try:
        await ensure_login(context)
        data = await scrape_missing_assignments(context, since_days=since_days)
        return {"count": len(data), "items": data}
    finally:
        await context.close()

@server.tool(ToolSpec(
    name="get_course_grades",
    description="Return grade history for a course over the last N days.",
    parameters=[
        ToolParam(name="course", type="string", description="Course name filter (e.g., 'Math').", required=False),
        ToolParam(name="since_days", type="integer", description="Days to include (default 14).", required=False),
    ],
))
async def get_course_grades(course: Optional[str] = None, since_days: int = 14):
    context = await get_context()
    try:
        await ensure_login(context)
        data = await scrape_course_grades(context, course_filter=course, since_days=since_days)
        return {"course_filter": course, "items": data}
    finally:
        await context.close()

@server.tool(ToolSpec(
    name="health",
    description="Check server health and portal reachability.",
    parameters=[],
))
async def health():
    return {"time": datetime.now().isoformat(), "base_url": PORTAL_BASE_URL, "state_file": os.path.abspath(STATE_PATH)}

# ---- Simple stdio event loop ----

async def main_stdio():
    import sys
    print("{\"ok\": true, \"message\": \"Homework MCP server ready\"}")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            resp = await server.handle(line)
        except Exception as e:
            resp = json.dumps({"error": str(e)})
        print(resp, flush=True)

if __name__ == "__main__":
    asyncio.run(main_stdio())
