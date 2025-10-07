#!/usr/bin/env python3
"""
Remote MCP Server for Infinite Campus
This version runs as a web service that can be accessed remotely
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from typing import List, Optional, Any
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
import hashlib
import hmac

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

# Security configuration
API_KEY = os.getenv("API_KEY") or keyring.get_password("homework-agent", "API_KEY")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,https://chat.openai.com").split(",")
SECRET_HEADER = os.getenv("SECRET_HEADER", "X-Homework-Agent")

# Log configuration
print(f"[CONFIG] Portal Base URL: {PORTAL_BASE_URL}", file=sys.stderr)
print(f"[CONFIG] Login URL: {FULL_LOGIN_URL}", file=sys.stderr)
print(f"[CONFIG] Username: {USERNAME}", file=sys.stderr)
print(f"[CONFIG] Password: {'Set' if PASSWORD else 'Not set'}", file=sys.stderr)
print(f"[CONFIG] Headless: {HEADLESS}", file=sys.stderr)
print(f"[CONFIG] Server: {HOST}:{PORT}", file=sys.stderr)
print(f"[CONFIG] API Key: {'Set' if API_KEY else 'Not set'}", file=sys.stderr)
print(f"[CONFIG] Allowed Origins: {ALLOWED_ORIGINS}", file=sys.stderr)

if not USERNAME or not PASSWORD:
    print("[WARN] Missing credentials. Set PORTAL_USERNAME/PORTAL_PASSWORD in .env or Keychain 'homework-agent'.", file=sys.stderr)

# Use LOGIN_URL if provided, otherwise construct from PORTAL_BASE_URL + LOGIN_PATH
FULL_LOGIN_URL = LOGIN_URL if LOGIN_URL else f"{PORTAL_BASE_URL}{LOGIN_PATH}"

# ---- Security Functions ----
security = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key from Authorization header"""
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API key not configured")
    
    if credentials.credentials != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return credentials

async def verify_custom_header(x_homework_agent: Optional[str] = Header(None)):
    """Verify custom header for additional security"""
    if not x_homework_agent:
        raise HTTPException(status_code=401, detail="Missing X-Homework-Agent header")
    
    # You can add more sophisticated header validation here
    if len(x_homework_agent) < 10:
        raise HTTPException(status_code=401, detail="Invalid X-Homework-Agent header")
    
    return x_homework_agent

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

# Add CORS middleware with security
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Restricted origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Homework-Agent"],
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
    """Wait for page to load with better error handling"""
    try:
        await page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception as e:
        print(f"[PAGE] Network idle timeout, continuing...", file=sys.stderr)

async def ensure_login(context: BrowserContext) -> None:
    print("[LOGIN] Starting login process...", file=sys.stderr)
    page = await context.new_page()
    
    try:
        # Go to main portal first
        print(f"[LOGIN] Going to portal: {PORTAL_BASE_URL}", file=sys.stderr)
        await page.goto(PORTAL_BASE_URL)
        await wait_for_page_load(page)
        
        # Check if already logged in
        logged_in_indicators = [
            "text=Logout",
            "text=Sign Out", 
            "text=Welcome",
            "text=Dashboard",
            "text=Grades",
            "[data-testid='logout']",
            ".logout-button"
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
        print("[LOGIN] Looking for Microsoft login form...", file=sys.stderr)
        
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
            await page.close()
            return
        
        # Click next
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
            await page.keyboard.press("Enter")
        
        # Wait for password page
        print("[LOGIN] Waiting for password page...", file=sys.stderr)
        await wait_for_page_load(page, 5000)
        
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
            await page.close()
            return
        
        # Click sign in
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
            await page.keyboard.press("Enter")
        
        # Wait for login to complete
        print("[LOGIN] Waiting for login to complete...", file=sys.stderr)
        await wait_for_page_load(page, 15000)
        
        print(f"[LOGIN] After login, URL: {page.url}", file=sys.stderr)
        
        # Save session
        await context.storage_state(path=STATE_PATH)
        print("[LOGIN] Session saved", file=sys.stderr)
        
    except Exception as e:
        print(f"[LOGIN] ERROR: {e}", file=sys.stderr)
        import traceback
        print(traceback.format_exc(), file=sys.stderr)
    finally:
        await page.close()

# ---- Scraping Functions ----
async def scrape_missing_assignments(context: BrowserContext, since_days: int = 14) -> List[Assignment]:
    print(f"[SCRAPE] Getting missing assignments (last {since_days} days)", file=sys.stderr)
    page = await context.new_page()
    
    try:
        assignments_url = f"{PORTAL_BASE_URL}/assignments"
        print(f"[SCRAPE] Going to: {assignments_url}", file=sys.stderr)
        await page.goto(assignments_url)
        await wait_for_page_load(page)
        
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
        grades_url = f"{PORTAL_BASE_URL}/grades"
        print(f"[SCRAPE] Going to: {grades_url}", file=sys.stderr)
        await page.goto(grades_url)
        await wait_for_page_load(page)
        
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

# ---- API Endpoints ----
@app.get("/")
async def root():
    return {
        "message": "Homework Agent MCP Server",
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

@app.get("/health")
async def health():
    return {
        "time": datetime.now().isoformat(),
        "base_url": PORTAL_BASE_URL,
        "login_url": FULL_LOGIN_URL,
        "state_file": os.path.abspath(STATE_PATH),
        "credentials_configured": bool(USERNAME and PASSWORD)
    }

@app.post("/tools/call", response_model=ToolResponse)
async def call_tool(
    request: ToolRequest,
    _: HTTPAuthorizationCredentials = Depends(verify_api_key),
    __: str = Depends(verify_custom_header)
):
    """Call a tool on the MCP server"""
    
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
                "credentials_configured": bool(USERNAME and PASSWORD)
            }
            return ToolResponse(success=True, data=result)
        
        else:
            return ToolResponse(success=False, error=f"Unknown tool: {request.tool}")
    
    except Exception as e:
        print(f"[API] Error: {e}", file=sys.stderr)
        return ToolResponse(success=False, error=str(e))

@app.get("/tools/list")
async def list_tools():
    """List available tools"""
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

if __name__ == "__main__":
    print(f"🚀 Starting Homework Agent MCP Server on {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)
