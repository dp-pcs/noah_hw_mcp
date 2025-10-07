#!/usr/bin/env python3
"""
Test browser automation with Infinite Campus
"""

import asyncio
import os
from dotenv import load_dotenv
from playwright.async_api import async_playwright

async def test_browser_automation():
    """Test browser automation with Infinite Campus"""
    
    load_dotenv()
    
    PORTAL_BASE_URL = os.getenv("PORTAL_BASE_URL")
    LOGIN_URL = os.getenv("LOGIN_URL")
    USERNAME = os.getenv("PORTAL_USERNAME")
    PASSWORD = os.getenv("PORTAL_PASSWORD")
    
    print("=== Browser Automation Test ===")
    print(f"Portal URL: {PORTAL_BASE_URL}")
    print(f"Login URL: {LOGIN_URL}")
    print(f"Username: {USERNAME}")
    print(f"Password: {'Set' if PASSWORD else 'Not set'}")
    
    if not all([PORTAL_BASE_URL, LOGIN_URL, USERNAME, PASSWORD]):
        print("❌ Missing configuration")
        return
    
    print("\n=== Starting Browser ===")
    
    try:
        async with async_playwright() as p:
            # Launch browser in non-headless mode so we can see what's happening
            browser = await p.chromium.launch(headless=False, slow_mo=1000)
            context = await browser.new_context()
            page = await context.new_page()
            
            print("✓ Browser launched")
            
            # Test 1: Go to login page
            print("\n=== Test 1: Navigating to Login Page ===")
            await page.goto(LOGIN_URL)
            print(f"✓ Navigated to: {page.url}")
            
            # Wait a bit to see the page
            await page.wait_for_timeout(3000)
            
            # Test 2: Look for login form elements
            print("\n=== Test 2: Analyzing Login Form ===")
            
            # Common Infinite Campus selectors
            username_selectors = [
                "input[name='username']",
                "input[name='user']", 
                "input[name='login']",
                "input[type='text']",
                "#username",
                "#user",
                "#login"
            ]
            
            password_selectors = [
                "input[name='password']",
                "input[name='pass']",
                "input[type='password']",
                "#password",
                "#pass"
            ]
            
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:has-text('Login')",
                "button:has-text('Sign In')",
                ".login-button",
                "#login-button"
            ]
            
            # Find username field
            username_field = None
            for selector in username_selectors:
                if await page.locator(selector).count() > 0:
                    username_field = selector
                    print(f"✓ Found username field: {selector}")
                    break
            
            if not username_field:
                print("❌ No username field found")
                print("Available input fields:")
                inputs = await page.locator("input").all()
                for i, input_elem in enumerate(inputs):
                    input_type = await input_elem.get_attribute("type")
                    input_name = await input_elem.get_attribute("name")
                    input_id = await input_elem.get_attribute("id")
                    print(f"  Input {i}: type='{input_type}', name='{input_name}', id='{input_id}'")
            
            # Find password field
            password_field = None
            for selector in password_selectors:
                if await page.locator(selector).count() > 0:
                    password_field = selector
                    print(f"✓ Found password field: {selector}")
                    break
            
            if not password_field:
                print("❌ No password field found")
            
            # Find submit button
            submit_button = None
            for selector in submit_selectors:
                if await page.locator(selector).count() > 0:
                    submit_button = selector
                    print(f"✓ Found submit button: {selector}")
                    break
            
            if not submit_button:
                print("❌ No submit button found")
                print("Available buttons:")
                buttons = await page.locator("button").all()
                for i, button in enumerate(buttons):
                    button_text = await button.inner_text()
                    button_type = await button.get_attribute("type")
                    print(f"  Button {i}: text='{button_text}', type='{button_type}'")
            
            # Test 3: Try to fill and submit (if we found the fields)
            if username_field and password_field and submit_button:
                print("\n=== Test 3: Attempting Login ===")
                try:
                    await page.fill(username_field, USERNAME)
                    print("✓ Filled username")
                    
                    await page.fill(password_field, PASSWORD)
                    print("✓ Filled password")
                    
                    await page.click(submit_button)
                    print("✓ Clicked submit")
                    
                    # Wait for navigation
                    await page.wait_for_load_state("networkidle")
                    print(f"✓ After login, URL: {page.url}")
                    
                    # Check if we're logged in (look for common logged-in indicators)
                    logged_in_indicators = [
                        "text=Logout",
                        "text=Sign Out", 
                        "text=Welcome",
                        "text=Dashboard",
                        "text=Grades",
                        "text=Assignments"
                    ]
                    
                    logged_in = False
                    for indicator in logged_in_indicators:
                        if await page.locator(indicator).count() > 0:
                            print(f"✓ Login successful! Found: {indicator}")
                            logged_in = True
                            break
                    
                    if not logged_in:
                        print("⚠️ Login may have failed - no clear success indicators found")
                        print("Current page title:", await page.title())
                    
                except Exception as e:
                    print(f"❌ Login attempt failed: {e}")
            else:
                print("❌ Cannot attempt login - missing form elements")
            
            # Keep browser open for a bit so you can see what happened
            print("\n=== Keeping browser open for 10 seconds ===")
            await page.wait_for_timeout(10000)
            
            await browser.close()
            print("✓ Browser closed")
            
    except Exception as e:
        print(f"❌ Browser automation error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_browser_automation())
