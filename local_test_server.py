#!/usr/bin/env python3
"""
Local test server for Homework Agent MCP Server
Run this locally to test the tools before deploying
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

# ---- Configuration ----
load_dotenv()
PORTAL_BASE_URL = os.getenv("PORTAL_BASE_URL", "https://academy20co.infinitecampus.org/campus/nav-wrapper/parent/portal/parent")
LOGIN_URL = os.getenv("LOGIN_URL", "https://academy20co.infinitecampus.org/campus/nav-wrapper/parent/portal/parent/login")
USERNAME = os.getenv("PORTAL_USERNAME") or keyring.get_password("homework-agent", "PORTAL_USERNAME")
PASSWORD = os.getenv("PORTAL_PASSWORD") or keyring.get_password("homework-agent", "PORTAL_PASSWORD")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Security configuration
API_KEY = os.getenv("API_KEY", "hw_agent_2024_secure_key_abc123xyz789")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,https://chat.openai.com").split(",")

# ---- Security Functions ----
security = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key from Authorization header"""
    if credentials.credentials != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials

async def verify_custom_header(x_homework_agent: Optional[str] = Header(None)):
    """Verify custom header for additional security"""
    if not x_homework_agent:
        raise HTTPException(status_code=401, detail="Missing X-Homework-Agent header")
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
    title="Homework Agent MCP Server (Local Test)",
    description="Local test server for Infinite Campus parent portal access",
    version="1.0.0"
)

# Add CORS middleware with security
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Homework-Agent"],
)

# ---- API Endpoints ----
@app.get("/")
async def root():
    return {
        "message": "Homework Agent MCP Server (Local Test)",
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
        "login_url": LOGIN_URL,
        "credentials_configured": bool(USERNAME and PASSWORD),
        "api_key_configured": bool(API_KEY)
    }

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
            # Return mock data for testing
            mock_assignments = [
                Assignment(
                    title="Math Worksheet - Chapter 5",
                    course="Pre-Algebra",
                    status="missing",
                    due_date=datetime.now() + timedelta(days=2),
                    points_possible=100.0
                ),
                Assignment(
                    title="Science Lab Report",
                    course="Science",
                    status="missing", 
                    due_date=datetime.now() + timedelta(days=5),
                    points_possible=50.0
                ),
                Assignment(
                    title="Spanish Vocabulary Quiz",
                    course="Spanish 2",
                    status="missing",
                    due_date=datetime.now() + timedelta(days=1),
                    points_possible=25.0
                )
            ]
            result = {
                "count": len(mock_assignments),
                "items": [item.model_dump() for item in mock_assignments]
            }
            return ToolResponse(success=True, data=result)
        
        elif request.tool == "get_course_grades":
            course = request.arguments.get("course")
            since_days = request.arguments.get("since_days", 14)
            # Return mock data for testing
            mock_grades = [
                GradeSample(
                    course="Pre-Algebra",
                    date=datetime.now() - timedelta(days=1),
                    grade_percent=85.5
                ),
                GradeSample(
                    course="Science",
                    date=datetime.now() - timedelta(days=3),
                    grade_percent=92.0
                ),
                GradeSample(
                    course="Spanish 2",
                    date=datetime.now() - timedelta(days=2),
                    grade_percent=78.5
                )
            ]
            
            # Filter by course if specified
            if course:
                mock_grades = [g for g in mock_grades if course.lower() in g.course.lower()]
            
            result = {
                "course_filter": course,
                "items": [item.model_dump() for item in mock_grades]
            }
            return ToolResponse(success=True, data=result)
        
        elif request.tool == "health":
            result = {
                "time": datetime.now().isoformat(),
                "base_url": PORTAL_BASE_URL,
                "login_url": LOGIN_URL,
                "credentials_configured": bool(USERNAME and PASSWORD),
                "api_key_configured": bool(API_KEY)
            }
            return ToolResponse(success=True, data=result)
        
        else:
            return ToolResponse(success=False, error=f"Unknown tool: {request.tool}")
    
    except Exception as e:
        print(f"[API] Error: {e}", file=sys.stderr)
        return ToolResponse(success=False, error=str(e))

if __name__ == "__main__":
    print(f"🚀 Starting Local Homework Agent MCP Server on {HOST}:{PORT}")
    print(f"🔑 API Key: {API_KEY}")
    print(f"🌐 Server URL: http://localhost:{PORT}")
    print(f"🔍 Health check: http://localhost:{PORT}/health")
    print(f"📋 Tools list: http://localhost:{PORT}/tools/list")
    uvicorn.run(app, host=HOST, port=PORT)
