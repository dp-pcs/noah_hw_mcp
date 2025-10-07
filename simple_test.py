#!/usr/bin/env python3
"""
Simple test to see the browser automation in action
"""

import asyncio
import os
from dotenv import load_dotenv
from playwright.async_api import async_playwright

async def test_infinite_campus_login():
    """Test Infinite Campus login with visible browser"""
    
    print("=== Infinite Campus Login Test ===")
    
    # Load configuration
    load_dotenv()
    PORTAL_BASE_URL = os.getenv("PORTAL_BASE_URL")
    LOGIN_URL = os.getenv("LOGIN_URL")
    USERNAME = os.getenv("PORTAL_USERNAME")
    PASSWORD = os.getenv("PORTAL_PASSWORD")
    
    print(f"Portal URL: {PORTAL_BASE_URL}")
    print(f"Login URL: {LOGIN_URL}")
    print(f"Username: {USERNAME}")
    print(f"Password: {'Set' if PASSWORD else 'Not set'}")
    
    if not all([PORTAL_BASE_URL, LOGIN_URL, USERNAME, PASSWORD]):
        print("❌ Missing configuration in .env file")
        return
    
    print("\n=== Starting Browser ===")
    
    try:
        async with async_playwright() as p:
            # Launch browser in visible mode
            print("Launching Chromium browser...")
            browser = await p.chromium.launch(
                headless=False,  # This makes it visible
                slow_mo=2000,    # Slow down actions so you can see them
                args=['--start-maximized']  # Start maximized
            )
            
            context = await browser.new_context()
            page = await context.new_page()
            
            print("✓ Browser launched successfully")
            
            # Step 1: Go to login page
            print(f"\n=== Step 1: Going to Login Page ===")
            print(f"Navigating to: {LOGIN_URL}")
            await page.goto(LOGIN_URL)
            
            # Wait for page to load
            await page.wait_for_load_state("networkidle")
            print(f"✓ Page loaded. Current URL: {page.url}")
            
            # Take screenshot
            await page.screenshot(path="step1_login_page.png")
            print("✓ Screenshot saved: step1_login_page.png")
            
            # Step 2: Analyze the page
            print(f"\n=== Step 2: Analyzing Login Form ===")
            
            # Look for username field
            username_selectors = [
                "input[name='username']",
                "input[name='user']",
                "input[type='text']",
                "#username",
                "#user",
                "input[placeholder*='username']",
                "input[placeholder*='user']"
            ]
            
            username_field = None
            for selector in username_selectors:
                count = await page.locator(selector).count()
                if count > 0:
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
                    input_placeholder = await input_elem.get_attribute("placeholder")
                    print(f"  Input {i}: type='{input_type}', name='{input_name}', id='{input_id}', placeholder='{input_placeholder}'")
            
            # Look for password field
            password_selectors = [
                "input[name='password']",
                "input[type='password']",
                "#password",
                "input[placeholder*='password']"
            ]
            
            password_field = None
            for selector in password_selectors:
                count = await page.locator(selector).count()
                if count > 0:
                    password_field = selector
                    print(f"✓ Found password field: {selector}")
                    break
            
            if not password_field:
                print("❌ No password field found")
            
            # Look for submit button
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:has-text('Login')",
                "button:has-text('Sign In')",
                "button:has-text('Submit')",
                ".login-button",
                "#login-button"
            ]
            
            submit_button = None
            for selector in submit_selectors:
                count = await page.locator(selector).count()
                if count > 0:
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
            
            # Step 3: Try to fill and submit
            if username_field and password_field and submit_button:
                print(f"\n=== Step 3: Attempting Login ===")
                
                print(f"Filling username field ({username_field})...")
                await page.fill(username_field, USERNAME)
                print("✓ Username filled")
                
                print(f"Filling password field ({password_field})...")
                await page.fill(password_field, PASSWORD)
                print("✓ Password filled")
                
                print(f"Clicking submit button ({submit_button})...")
                await page.click(submit_button)
                print("✓ Submit clicked")
                
                # Wait for navigation
                print("Waiting for login to complete...")
                await page.wait_for_load_state("networkidle")
                
                # Take screenshot after login
                await page.screenshot(path="step3_after_login.png")
                print("✓ Screenshot saved: step3_after_login.png")
                
                print(f"✓ After login, URL: {page.url}")
                
                # Check for success indicators
                success_indicators = [
                    "text=Logout",
                    "text=Sign Out",
                    "text=Welcome",
                    "text=Dashboard",
                    "text=Grades",
                    "text=Assignments"
                ]
                
                login_successful = False
                for indicator in success_indicators:
                    count = await page.locator(indicator).count()
                    if count > 0:
                        print(f"✓ Login successful! Found indicator: {indicator}")
                        login_successful = True
                        break
                
                if not login_successful:
                    print("⚠️ Login may have failed - no clear success indicators found")
                    print("Check the screenshots to see what happened")
                
            else:
                print("❌ Cannot attempt login - missing form elements")
                print("Check the screenshots to see the page structure")
            
            # Keep browser open for a bit
            print(f"\n=== Browser will stay open for 30 seconds ===")
            print("You can manually interact with the page if needed")
            await page.wait_for_timeout(30000)
            
            await browser.close()
            print("✓ Browser closed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("This test will open a browser window so you can see what's happening")
    print("Press Ctrl+C to stop early if needed")
    print()
    
    try:
        asyncio.run(test_infinite_campus_login())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    
    print("\n=== Test Complete ===")
    print("Check the generated screenshots:")
    print("- step1_login_page.png")
    print("- step3_after_login.png")