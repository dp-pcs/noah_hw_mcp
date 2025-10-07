#!/usr/bin/env python3
"""
Configured MCP Server for Infinite Campus with real data scraping
This version uses the specific URLs you identified in locations.md
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from typing import List, Optional, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

import keyring
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from playwright.async_api import async_playwright, BrowserContext, Page

# ---- Configuration ----
load_dotenv()
PORTAL_BASE_URL = os.getenv("PORTAL_BASE_URL", "https://portal.example.edu")
LOGIN_URL = os.getenv("LOGIN_URL")
LOGIN_PATH = os.getenv("LOGIN_PATH", "/login")
USERNAME = os.getenv("PORTAL_USERNAME") or keyring.get_password("homework-agent", "PORTAL_USERNAME")
PASSWORD = os.getenv("PORTAL_PASSWORD") or keyring.get_password("homework-agent", "PORTAL_PASSWORD")
STATE_PATH = os.getenv("STATE_PATH", "./state.json")
HEADLESS = os.getenv("HEADLESS", "true").lower() != "false"
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Use LOGIN_URL if provided, otherwise construct from PORTAL_BASE_URL + LOGIN_PATH
FULL_LOGIN_URL = LOGIN_URL if LOGIN_URL else f"{PORTAL_BASE_URL}{LOGIN_PATH}"

# Specific URLs from your locations.md
INFINITE_CAMPUS_URLS = {
    "grades_overview": "https://academy20co.infinitecampus.org/campus/nav-wrapper/parent/portal/parent/grades?appName=academy20",
    "assignments_all": "https://academy20co.infinitecampus.org/campus/nav-wrapper/parent/portal/parent/assignment-list?appName=academy20",
    "assignments_missing": "https://academy20co.infinitecampus.org/campus/nav-wrapper/parent/portal/parent/assignment-list?missingFilter=true&appName=academy20",
    "classes": {
        "individuals_and_societies": "https://academy20co.infinitecampus.org/campus/nav-wrapper/parent/portal/parent/classroom/grades/student-grades?showAllTerms=false&selectedTermID=4928&classroomSectionID=2203804&appName=academy20",
        "lang_lit": "https://academy20co.infinitecampus.org/campus/nav-wrapper/parent/portal/parent/classroom/grades/student-grades?showAllTerms=false&selectedTermID=4928&classroomSectionID=2203759&appName=academy20",
        "science": "https://academy20co.infinitecampus.org/campus/nav-wrapper/parent/portal/parent/classroom/grades/student-grades?showAllTerms=false&selectedTermID=4928&classroomSectionID=2203787&appName=academy20",
        "spanish_2": "https://academy20co.infinitecampus.org/campus/nav-wrapper/parent/portal/parent/classroom/grades/student-grades?showAllTerms=false&selectedTermID=4928&classroomSectionID=2203715&appName=academy20",
        "pre_algebra": "https://academy20co.infinitecampus.org/campus/nav-wrapper/parent/portal/parent/classroom/grades/student-grades?showAllTerms=false&selectedTermID=4928&classroomSectionID=2203700&appName=academy20"
    }
}

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

class ToolRequest(BaseModel):
    tool: str
    arguments: dict = {}

class ToolResponse(BaseModel):
    success: bool
    data: Any = None
    error: Optional[str] = None

# ---- FastAPI App ----
app = FastAPI(
    title="Homework Agent MCP Server",
    description="MCP Server for Infinite Campus parent portal access",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    try:
        await page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception as e:
        print(f"[PAGE] Network idle timeout, continuing...", file=sys.stderr)

async def ensure_login(context: BrowserContext) -> None:
    print("[LOGIN] Starting login process...", file=sys.stderr)
    page = await context.new_page()
    
    try:
        await page.goto(PORTAL_BASE_URL)
        await wait_for_page_load(page)
        
        # Check if already logged in
        logged_in_indicators = [
            "text=Logout", "text=Sign Out", "text=Welcome", "text=Dashboard", "text=Grades"
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
        
        # Microsoft login process
        print("[LOGIN] Performing Microsoft login...", file=sys.stderr)
        
        # Username
        await page.fill("input[name='loginfmt']", USERNAME)
        await page.click("input[type='submit']")
        await wait_for_page_load(page, 5000)
        
        # Password
        await page.fill("input[name='passwd']", PASSWORD)
        await page.click("input[type='submit']")
        await wait_for_page_load(page, 15000)
        
        print(f"[LOGIN] After login, URL: {page.url}", file=sys.stderr)
        
        # Save session
        await context.storage_state(path=STATE_PATH)
        print("[LOGIN] Session saved", file=sys.stderr)
        
    except Exception as e:
        print(f"[LOGIN] ERROR: {e}", file=sys.stderr)
    finally:
        await page.close()

# ---- Real Data Scraping Functions ----
async def scrape_missing_assignments(context: BrowserContext, since_days: int = 14) -> List[Assignment]:
    print(f"[SCRAPE] Getting missing assignments (last {since_days} days)", file=sys.stderr)
    page = await context.new_page()
    
    try:
        url = INFINITE_CAMPUS_URLS["assignments_missing"]
        print(f"[SCRAPE] Going to: {url}", file=sys.stderr)
        await page.goto(url)
        await wait_for_page_load(page)
        
        # Take screenshot for debugging
        await page.screenshot(path="assignments_page_debug.png")
        print("[SCRAPE] Screenshot saved as assignments_page_debug.png", file=sys.stderr)
        
        assignments = []
        cutoff_date = datetime.now() - timedelta(days=since_days)
        
        # Look for assignment tables - try multiple selectors
        table_selectors = [
            "table",
            ".assignment-table",
            ".data-table",
            ".table",
            "[role='table']",
            ".ic-table"
        ]
        
        table_found = None
        for selector in table_selectors:
            if await page.locator(selector).count() > 0:
                table_found = selector
                print(f"[SCRAPE] Found table with selector: {selector}", file=sys.stderr)
                break
        
        if not table_found:
            print("[SCRAPE] No table found, looking for assignment cards...", file=sys.stderr)
            # Try card-based layout
            card_selectors = [
                ".assignment-card",
                ".assignment-item",
                ".card",
                "[data-testid*='assignment']"
            ]
            
            for selector in card_selectors:
                if await page.locator(selector).count() > 0:
                    print(f"[SCRAPE] Found assignment cards with selector: {selector}", file=sys.stderr)
                    # Process cards
                    cards = await page.locator(selector).all()
                    for i, card in enumerate(cards):
                        try:
                            # Extract data from card
                            title_elem = await card.locator("h3, .title, .assignment-title, [data-testid*='title']").first
                            course_elem = await card.locator(".course, .subject, .class-name").first
                            status_elem = await card.locator(".status, .assignment-status, .missing").first
                            due_date_elem = await card.locator(".due-date, .due, .date").first
                            
                            title = await title_elem.inner_text() if await title_elem.count() > 0 else f"Assignment {i+1}"
                            course = await course_elem.inner_text() if await course_elem.count() > 0 else "Unknown"
                            status = await status_elem.inner_text() if await status_elem.count() > 0 else "missing"
                            due_date_text = await due_date_elem.inner_text() if await due_date_elem.count() > 0 else None
                            
                            # Parse due date
                            due_date = None
                            if due_date_text:
                                try:
                                    for fmt in ["%m/%d/%Y", "%Y-%m-%d", "%b %d, %Y", "%m-%d-%Y", "%m/%d/%y"]:
                                        try:
                                            due_date = datetime.strptime(due_date_text.strip(), fmt)
                                            break
                                        except:
                                            continue
                                except:
                                    pass
                            
                            if due_date is None or due_date >= cutoff_date:
                                assignment = Assignment(
                                    title=title.strip(),
                                    course=course.strip(),
                                    due_date=due_date,
                                    status="missing"
                                )
                                assignments.append(assignment)
                                print(f"[SCRAPE] Found missing assignment: {title} ({course})", file=sys.stderr)
                        
                        except Exception as e:
                            print(f"[SCRAPE] Error processing card {i}: {e}", file=sys.stderr)
                            continue
                    break
        
        else:
            # Process table-based layout
            table = await page.locator(table_found).first
            rows = await table.locator("tr").all()
            print(f"[SCRAPE] Found {len(rows)} rows in table", file=sys.stderr)
            
            for i, row in enumerate(rows):
                try:
                    # Skip header row
                    if i == 0:
                        continue
                    
                    # Get all cells in the row
                    cells = await row.locator("td").all()
                    if len(cells) < 3:
                        continue
                    
                    # Extract data from cells (adjust indices based on your table structure)
                    title = await cells[0].inner_text() if len(cells) > 0 else f"Assignment {i}"
                    course = await cells[1].inner_text() if len(cells) > 1 else "Unknown"
                    due_date_text = await cells[2].inner_text() if len(cells) > 2 else None
                    status = await cells[3].inner_text() if len(cells) > 3 else "missing"
                    
                    # Parse due date
                    due_date = None
                    if due_date_text:
                        try:
                            for fmt in ["%m/%d/%Y", "%Y-%m-%d", "%b %d, %Y", "%m-%d-%Y", "%m/%d/%y"]:
                                try:
                                    due_date = datetime.strptime(due_date_text.strip(), fmt)
                                    break
                                except:
                                    continue
                        except:
                            pass
                    
                    if due_date is None or due_date >= cutoff_date:
                        assignment = Assignment(
                            title=title.strip(),
                            course=course.strip(),
                            due_date=due_date,
                            status="missing"
                        )
                        assignments.append(assignment)
                        print(f"[SCRAPE] Found missing assignment: {title} ({course})", file=sys.stderr)
                
                except Exception as e:
                    print(f"[SCRAPE] Error processing row {i}: {e}", file=sys.stderr)
                    continue
        
        print(f"[SCRAPE] Found {len(assignments)} missing assignments", file=sys.stderr)
        return assignments
        
    except Exception as e:
        print(f"[SCRAPE] ERROR: {e}", file=sys.stderr)
        return []
    finally:
        await page.close()

async def scrape_course_grades(context: BrowserContext, course_filter: Optional[str], since_days: int = 14) -> List[GradeSample]:
    print(f"[SCRAPE] Getting course grades (last {since_days} days)", file=sys.stderr)
    page = await context.new_page()
    
    try:
        grades = []
        cutoff_date = datetime.now() - timedelta(days=since_days)
        
        # If specific course requested, go to that course page
        if course_filter:
            course_mapping = {
                "individuals": "individuals_and_societies",
                "societies": "individuals_and_societies",
                "lang": "lang_lit",
                "lit": "lang_lit",
                "language": "lang_lit",
                "literature": "lang_lit",
                "science": "science",
                "spanish": "spanish_2",
                "math": "pre_algebra",
                "algebra": "pre_algebra",
                "pre-algebra": "pre_algebra"
            }
            
            # Find matching course
            course_key = None
            for key, value in course_mapping.items():
                if key.lower() in course_filter.lower():
                    course_key = value
                    break
            
            if course_key and course_key in INFINITE_CAMPUS_URLS["classes"]:
                url = INFINITE_CAMPUS_URLS["classes"][course_key]
                print(f"[SCRAPE] Going to specific course: {course_key} - {url}", file=sys.stderr)
                await page.goto(url)
                await wait_for_page_load(page)
                
                # Take screenshot for debugging
                await page.screenshot(path=f"grades_{course_key}_debug.png")
                print(f"[SCRAPE] Screenshot saved as grades_{course_key}_debug.png", file=sys.stderr)
                
                # Extract grades from this specific course
                course_grades = await extract_grades_from_page(page, course_key, cutoff_date)
                grades.extend(course_grades)
            else:
                print(f"[SCRAPE] Course '{course_filter}' not found, getting all grades", file=sys.stderr)
                # Fall through to get all grades
        else:
            # Get all grades from overview page
            url = INFINITE_CAMPUS_URLS["grades_overview"]
            print(f"[SCRAPE] Going to grades overview: {url}", file=sys.stderr)
            await page.goto(url)
            await wait_for_page_load(page)
            
            # Take screenshot for debugging
            await page.screenshot(path="grades_overview_debug.png")
            print("[SCRAPE] Screenshot saved as grades_overview_debug.png", file=sys.stderr)
            
            # Extract grades from overview page
            overview_grades = await extract_grades_from_page(page, "overview", cutoff_date)
            grades.extend(overview_grades)
        
        print(f"[SCRAPE] Found {len(grades)} recent grades", file=sys.stderr)
        return grades
        
    except Exception as e:
        print(f"[SCRAPE] ERROR: {e}", file=sys.stderr)
        return []
    finally:
        await page.close()

async def extract_grades_from_page(page: Page, course_name: str, cutoff_date: datetime) -> List[GradeSample]:
    """Extract grades from a specific page"""
    grades = []
    
    try:
        # Look for grade tables
        table_selectors = [
            "table",
            ".grade-table",
            ".data-table",
            ".table",
            "[role='table']",
            ".ic-table"
        ]
        
        table_found = None
        for selector in table_selectors:
            if await page.locator(selector).count() > 0:
                table_found = selector
                print(f"[SCRAPE] Found grade table with selector: {selector}", file=sys.stderr)
                break
        
        if table_found:
            table = await page.locator(table_found).first
            rows = await table.locator("tr").all()
            print(f"[SCRAPE] Found {len(rows)} rows in grade table", file=sys.stderr)
            
            for i, row in enumerate(rows):
                try:
                    # Skip header row
                    if i == 0:
                        continue
                    
                    # Get all cells in the row
                    cells = await row.locator("td").all()
                    if len(cells) < 2:
                        continue
                    
                    # Extract data from cells
                    grade_text = await cells[0].inner_text() if len(cells) > 0 else None
                    date_text = await cells[1].inner_text() if len(cells) > 1 else None
                    description_text = await cells[2].inner_text() if len(cells) > 2 else None
                    
                    # Parse grade
                    grade_percent = None
                    if grade_text:
                        try:
                            import re
                            numbers = re.findall(r'\d+\.?\d*', grade_text)
                            if numbers:
                                grade_percent = float(numbers[0])
                        except:
                            pass
                    
                    # Parse date
                    grade_date = datetime.now()
                    if date_text:
                        try:
                            for fmt in ["%m/%d/%Y", "%Y-%m-%d", "%b %d, %Y", "%m-%d-%Y", "%m/%d/%y"]:
                                try:
                                    grade_date = datetime.strptime(date_text.strip(), fmt)
                                    break
                                except:
                                    continue
                        except:
                            pass
                    
                    # Only include recent grades
                    if grade_date >= cutoff_date:
                        grade_sample = GradeSample(
                            course=course_name.replace("_", " ").title(),
                            date=grade_date,
                            grade_percent=grade_percent
                        )
                        grades.append(grade_sample)
                        print(f"[SCRAPE] Found grade: {course_name} - {grade_percent}% ({grade_date})", file=sys.stderr)
                
                except Exception as e:
                    print(f"[SCRAPE] Error processing grade row {i}: {e}", file=sys.stderr)
                    continue
    
    except Exception as e:
        print(f"[SCRAPE] Error extracting grades: {e}", file=sys.stderr)
    
    return grades

# ---- API Endpoints ----
@app.get("/")
async def root():
    return {
        "message": "Homework Agent MCP Server (Configured with specific URLs)",
        "version": "1.0.0",
        "status": "running",
        "tools": ["check_missing_assignments", "get_course_grades", "health"],
        "configured_urls": list(INFINITE_CAMPUS_URLS.keys())
    }

@app.get("/health")
async def health():
    return {
        "time": datetime.now().isoformat(),
        "base_url": PORTAL_BASE_URL,
        "login_url": FULL_LOGIN_URL,
        "state_file": os.path.abspath(STATE_PATH),
        "credentials_configured": bool(USERNAME and PASSWORD),
        "configured_urls": list(INFINITE_CAMPUS_URLS.keys())
    }

@app.post("/tools/call", response_model=ToolResponse)
async def call_tool(request: ToolRequest):
    print(f"[API] Tool call: {request.tool} with args: {request.arguments}", file=sys.stderr)
    
    try:
        if request.tool == "check_missing_assignments":
            since_days = request.arguments.get("since_days", 14)
            context = await get_context()
            try:
                await ensure_login(context)
                data = await scrape_missing_assignments(context, since_days=since_days)
                result = {
                    "count": len(data),
                    "items": [item.model_dump() for item in data]
                }
                return ToolResponse(success=True, data=result)
            finally:
                await context.close()
        
        elif request.tool == "get_course_grades":
            course = request.arguments.get("course")
            since_days = request.arguments.get("since_days", 14)
            context = await get_context()
            try:
                await ensure_login(context)
                data = await scrape_course_grades(context, course_filter=course, since_days=since_days)
                result = {
                    "course_filter": course,
                    "items": [item.model_dump() for item in data]
                }
                return ToolResponse(success=True, data=result)
            finally:
                await context.close()
        
        elif request.tool == "health":
            result = {
                "time": datetime.now().isoformat(),
                "base_url": PORTAL_BASE_URL,
                "login_url": FULL_LOGIN_URL,
                "state_file": os.path.abspath(STATE_PATH),
                "credentials_configured": bool(USERNAME and PASSWORD),
                "configured_urls": list(INFINITE_CAMPUS_URLS.keys())
            }
            return ToolResponse(success=True, data=result)
        
        else:
            return ToolResponse(success=False, error=f"Unknown tool: {request.tool}")
    
    except Exception as e:
        print(f"[API] Error: {e}", file=sys.stderr)
        return ToolResponse(success=False, error=str(e))

@app.get("/tools/list")
async def list_tools():
    return {
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
                        "description": "Course name filter (e.g., 'Math', 'Science', 'Spanish')."
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

if __name__ == "__main__":
    print(f"🚀 Starting Configured Homework Agent MCP Server on {HOST}:{PORT}")
    print(f"📋 Configured with specific Infinite Campus URLs", file=sys.stderr)
    uvicorn.run(app, host=HOST, port=PORT)
