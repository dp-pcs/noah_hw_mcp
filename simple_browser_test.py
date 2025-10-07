#!/usr/bin/env python3
"""
Simple browser test that writes output to file
"""

import asyncio
import os
from dotenv import load_dotenv
from playwright.async_api import async_playwright

async def test_infinite_campus():
    load_dotenv()
    
    PORTAL_BASE_URL = os.getenv("PORTAL_BASE_URL")
    LOGIN_URL = os.getenv("LOGIN_URL")
    USERNAME = os.getenv("PORTAL_USERNAME")
    PASSWORD = os.getenv("PORTAL_PASSWORD")
    
    with open("browser_test_results.txt", "w") as f:
        f.write("=== Infinite Campus Browser Test ===\n")
        f.write(f"Portal URL: {PORTAL_BASE_URL}\n")
        f.write(f"Login URL: {LOGIN_URL}\n")
        f.write(f"Username: {USERNAME}\n")
        f.write(f"Password: {'Set' if PASSWORD else 'Not set'}\n\n")
        
        try:
            async with async_playwright() as p:
                f.write("Starting browser...\n")
                browser = await p.chromium.launch(headless=False, slow_mo=2000)
                context = await browser.new_context()
                page = await context.new_page()
                
                f.write("Navigating to login page...\n")
                await page.goto(LOGIN_URL)
                f.write(f"Current URL: {page.url}\n")
                
                # Wait and take screenshot
                await page.wait_for_timeout(5000)
                await page.screenshot(path="infinite_campus_login.png")
                f.write("Screenshot saved as infinite_campus_login.png\n")
                
                # Look for form elements
                f.write("\n=== Form Analysis ===\n")
                
                # Check for username fields
                username_candidates = [
                    "input[name='username']",
                    "input[name='user']",
                    "input[type='text']",
                    "#username",
                    "#user"
                ]
                
                for selector in username_candidates:
                    count = await page.locator(selector).count()
                    f.write(f"Username selector '{selector}': {count} found\n")
                
                # Check for password fields
                password_candidates = [
                    "input[name='password']",
                    "input[type='password']",
                    "#password"
                ]
                
                for selector in password_candidates:
                    count = await page.locator(selector).count()
                    f.write(f"Password selector '{selector}': {count} found\n")
                
                # Check for submit buttons
                submit_candidates = [
                    "button[type='submit']",
                    "input[type='submit']",
                    "button:has-text('Login')",
                    "button:has-text('Sign In')"
                ]
                
                for selector in submit_candidates:
                    count = await page.locator(selector).count()
                    f.write(f"Submit selector '{selector}': {count} found\n")
                
                # Get page title and some text
                title = await page.title()
                f.write(f"\nPage title: {title}\n")
                
                # Try to get some text content
                try:
                    body_text = await page.locator("body").inner_text()
                    f.write(f"Page contains text: {body_text[:500]}...\n")
                except:
                    f.write("Could not get page text\n")
                
                f.write("\nKeeping browser open for 15 seconds...\n")
                await page.wait_for_timeout(15000)
                
                await browser.close()
                f.write("Browser closed successfully\n")
                
        except Exception as e:
            f.write(f"Error: {e}\n")
            import traceback
            f.write(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test_infinite_campus())
    print("Test completed. Check browser_test_results.txt and infinite_campus_login.png")
