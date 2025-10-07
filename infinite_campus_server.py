#!/usr/bin/env python3
"""
Real Infinite Campus MCP Server - Actually scrapes data
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from typing import List, Optional

from dotenv import load_dotenv
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

# Load environment variables
load_dotenv()

# Configuration
PORTAL_BASE_URL = os.getenv("PORTAL_BASE_URL", "https://academy20co.infinitecampus.org")
LOGIN_URL = os.getenv("LOGIN_URL", "https://academy20co.infinitecampus.org/campus/SSO/academy20/portal/parents?configID=2")
USERNAME = os.getenv("PORTAL_USERNAME")
PASSWORD = os.getenv("PORTAL_PASSWORD")
HEADLESS = os.getenv("HEADLESS", "true").lower() != "false"
STATE_PATH = os.getenv("STATE_PATH", "./state.json")

# Infinite Campus URLs from locations.md
GRADES_URL = "https://academy20co.infinitecampus.org/campus/nav-wrapper/parent/portal/parent/grades?appName=academy20"
ASSIGNMENTS_URL = "https://academy20co.infinitecampus.org/campus/nav-wrapper/parent/portal/parent/assignment-list?appName=academy20"
MISSING_ASSIGNMENTS_URL = "https://academy20co.infinitecampus.org/campus/nav-wrapper/parent/portal/parent/assignment-list?missingFilter=true&appName=academy20"

print(f"[CONFIG] Portal Base URL: {PORTAL_BASE_URL}", file=sys.stderr)
print(f"[CONFIG] Login URL: {LOGIN_URL}", file=sys.stderr)
print(f"[CONFIG] Username: {USERNAME}", file=sys.stderr)
print(f"[CONFIG] Password: {'Set' if PASSWORD else 'Not set'}", file=sys.stderr)
print(f"[CONFIG] Headless: {HEADLESS}", file=sys.stderr)

if not USERNAME or not PASSWORD:
    print("[ERROR] Missing credentials! Set PORTAL_USERNAME and PORTAL_PASSWORD in .env", file=sys.stderr)
    sys.exit(1)

class InfiniteCampusScraper:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        
    async def start(self):
        """Start the browser"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=HEADLESS)
        self.context = await self.browser.new_context()
        print("[BROWSER] Browser started", file=sys.stderr)
        
    async def stop(self):
        """Stop the browser"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        print("[BROWSER] Browser stopped", file=sys.stderr)
    
    async def login(self) -> bool:
        """Login to Infinite Campus"""
        try:
            print(f"[LOGIN] Navigating to {LOGIN_URL}", file=sys.stderr)
            page = await self.context.new_page()
            await page.goto(LOGIN_URL, wait_until="networkidle")
            
            # Wait for Microsoft login page
            print("[LOGIN] Waiting for Microsoft login form", file=sys.stderr)
            await page.wait_for_selector('input[name="loginfmt"]', timeout=10000)
            
            # Enter username
            print(f"[LOGIN] Entering username: {USERNAME}", file=sys.stderr)
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
            await page.wait_for_load_state("networkidle")
            
            # Check if we're logged in by looking for the grades page
            current_url = page.url
            print(f"[LOGIN] Current URL: {current_url}", file=sys.stderr)
            
            if "portal" in current_url or "grades" in current_url:
                print("[LOGIN] ✅ Login successful!", file=sys.stderr)
                await page.close()
                return True
            else:
                print(f"[LOGIN] ❌ Login failed - unexpected URL: {current_url}", file=sys.stderr)
                await page.screenshot(path="login_failed.png")
                await page.close()
                return False
                
        except Exception as e:
            print(f"[LOGIN] ❌ Login error: {e}", file=sys.stderr)
            return False
    
    async def get_missing_assignments(self, since_days: int = 14) -> List[dict]:
        """Get missing assignments"""
        try:
            print(f"[SCRAPE] Getting missing assignments from {MISSING_ASSIGNMENTS_URL}", file=sys.stderr)
            page = await self.context.new_page()
            await page.goto(MISSING_ASSIGNMENTS_URL, wait_until="networkidle")
            
            # Wait for the assignments table to load
            await page.wait_for_selector('table, .assignment-list, [class*="assignment"]', timeout=10000)
            
            # Take a screenshot for debugging
            await page.screenshot(path="missing_assignments.png")
            print("[SCRAPE] Screenshot saved to missing_assignments.png", file=sys.stderr)
            
            # Extract assignments from the page
            # This is a placeholder - we need to inspect the actual HTML structure
            assignments = await page.evaluate('''() => {
                const assignments = [];
                
                // Try to find assignment rows
                const rows = document.querySelectorAll('tr[class*="assignment"], .assignment-row, table tr');
                
                rows.forEach(row => {
                    const cells = row.querySelectorAll('td');
                    if (cells.length >= 3) {
                        const title = cells[0]?.textContent?.trim() || '';
                        const course = cells[1]?.textContent?.trim() || '';
                        const dueDate = cells[2]?.textContent?.trim() || '';
                        
                        if (title && title !== 'Assignment' && title !== 'Title') {
                            assignments.push({
                                title: title,
                                course: course,
                                due_date: dueDate,
                                status: 'missing'
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
            print(f"[SCRAPE] Getting grades from {GRADES_URL}", file=sys.stderr)
            page = await self.context.new_page()
            await page.goto(GRADES_URL, wait_until="networkidle")
            
            # Wait for the grades table to load
            await page.wait_for_selector('table, .grade-list, [class*="grade"]', timeout=10000)
            
            # Take a screenshot for debugging
            await page.screenshot(path="grades.png")
            print("[SCRAPE] Screenshot saved to grades.png", file=sys.stderr)
            
            # Extract grades from the page
            grades = await page.evaluate('''() => {
                const grades = [];
                
                // Try to find grade rows
                const rows = document.querySelectorAll('tr[class*="grade"], .grade-row, table tr');
                
                rows.forEach(row => {
                    const cells = row.querySelectorAll('td');
                    if (cells.length >= 2) {
                        const course = cells[0]?.textContent?.trim() || '';
                        const grade = cells[1]?.textContent?.trim() || '';
                        
                        if (course && course !== 'Course' && course !== 'Class') {
                            grades.push({
                                course: course,
                                grade: grade,
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

async def main():
    """Main function"""
    scraper = InfiniteCampusScraper()
    
    try:
        # Start browser
        await scraper.start()
        
        # Login
        if not await scraper.login():
            print("[ERROR] Login failed!", file=sys.stderr)
            return
        
        # Get missing assignments
        print("\n[TEST] Getting missing assignments...", file=sys.stderr)
        assignments = await scraper.get_missing_assignments()
        print(f"\n📋 Missing Assignments ({len(assignments)}):", file=sys.stderr)
        for assignment in assignments:
            print(f"  - {assignment['title']} ({assignment['course']}) - Due: {assignment['due_date']}", file=sys.stderr)
        
        # Get grades
        print("\n[TEST] Getting grades...", file=sys.stderr)
        grades = await scraper.get_grades()
        print(f"\n📊 Grades ({len(grades)}):", file=sys.stderr)
        for grade in grades:
            print(f"  - {grade['course']}: {grade['grade']}", file=sys.stderr)
        
    finally:
        await scraper.stop()

if __name__ == "__main__":
    asyncio.run(main())
