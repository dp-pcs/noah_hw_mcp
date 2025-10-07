#!/usr/bin/env python3
"""
Interactive script to configure Infinite Campus data scraping
This will help you find the right selectors for your specific portal
"""

import asyncio
import os
from playwright.async_api import async_playwright

async def analyze_infinite_campus():
    """Analyze Infinite Campus portal to find the right selectors"""
    
    print("🔍 Infinite Campus Scraping Configuration Tool")
    print("=" * 50)
    print()
    
    # Load configuration
    from dotenv import load_dotenv
    load_dotenv()
    
    PORTAL_BASE_URL = os.getenv("PORTAL_BASE_URL")
    USERNAME = os.getenv("PORTAL_USERNAME")
    PASSWORD = os.getenv("PORTAL_PASSWORD")
    
    if not all([PORTAL_BASE_URL, USERNAME, PASSWORD]):
        print("❌ Missing configuration. Please set up your .env file first.")
        return
    
    print(f"Portal: {PORTAL_BASE_URL}")
    print(f"Username: {USERNAME}")
    print()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=2000)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Step 1: Login
            print("🔐 Step 1: Logging in...")
            await page.goto(PORTAL_BASE_URL)
            await page.wait_for_load_state("networkidle")
            
            # Microsoft login process
            await page.fill("input[name='loginfmt']", USERNAME)
            await page.click("input[type='submit']")
            await page.wait_for_load_state("networkidle")
            
            await page.fill("input[name='passwd']", PASSWORD)
            await page.click("input[type='submit']")
            await page.wait_for_load_state("networkidle")
            
            print("✅ Login successful!")
            await page.screenshot(path="logged_in_dashboard.png")
            print("📸 Screenshot saved: logged_in_dashboard.png")
            
            # Step 2: Analyze navigation
            print("\n🧭 Step 2: Analyzing navigation...")
            print("Looking for navigation menu...")
            
            # Common Infinite Campus navigation selectors
            nav_selectors = [
                "nav",
                ".navigation",
                ".nav-menu",
                ".main-nav",
                "[role='navigation']",
                ".menu",
                ".sidebar"
            ]
            
            nav_found = False
            for selector in nav_selectors:
                if await page.locator(selector).count() > 0:
                    print(f"✅ Found navigation: {selector}")
                    nav_found = True
                    break
            
            if not nav_found:
                print("⚠️ No clear navigation found, looking for links...")
            
            # Look for grades/assignments links
            print("\n📊 Step 3: Looking for Grades/Assignments links...")
            
            grades_keywords = ["grades", "gradebook", "assignments", "homework", "academic"]
            found_links = []
            
            for keyword in grades_keywords:
                # Look for links containing these keywords
                links = await page.locator(f"a:has-text('{keyword}')").all()
                for i, link in enumerate(links):
                    text = await link.inner_text()
                    href = await link.get_attribute("href")
                    print(f"  Found link: '{text}' -> {href}")
                    found_links.append({"text": text, "href": href, "keyword": keyword})
            
            # Step 4: Test Grades page
            print("\n📈 Step 4: Testing Grades page...")
            
            # Try to find and click grades link
            grades_clicked = False
            for link_info in found_links:
                if "grade" in link_info["keyword"].lower():
                    try:
                        print(f"Clicking on: {link_info['text']}")
                        await page.click(f"a:has-text('{link_info['text']}')")
                        await page.wait_for_load_state("networkidle")
                        await page.screenshot(path="grades_page.png")
                        print("📸 Screenshot saved: grades_page.png")
                        grades_clicked = True
                        break
                    except:
                        continue
            
            if not grades_clicked:
                print("⚠️ Could not find grades link, trying common URLs...")
                grades_urls = [
                    f"{PORTAL_BASE_URL}/grades",
                    f"{PORTAL_BASE_URL}/gradebook",
                    f"{PORTAL_BASE_URL}/academic",
                    f"{PORTAL_BASE_URL}/student/grades"
                ]
                
                for url in grades_urls:
                    try:
                        print(f"Trying URL: {url}")
                        await page.goto(url)
                        await page.wait_for_load_state("networkidle")
                        await page.screenshot(path="grades_page.png")
                        print("📸 Screenshot saved: grades_page.png")
                        break
                    except:
                        continue
            
            # Step 5: Analyze grades page structure
            print("\n🔍 Step 5: Analyzing grades page structure...")
            
            # Look for grade tables
            table_selectors = [
                "table",
                ".grade-table",
                ".grades-table",
                ".academic-table",
                "[data-testid*='grade']",
                ".course-grades"
            ]
            
            tables_found = []
            for selector in table_selectors:
                count = await page.locator(selector).count()
                if count > 0:
                    print(f"✅ Found {count} table(s) with selector: {selector}")
                    tables_found.append(selector)
            
            # Look for course names
            course_selectors = [
                ".course-name",
                ".subject",
                ".class-name",
                "td:first-child",
                "[data-testid*='course']"
            ]
            
            courses_found = []
            for selector in course_selectors:
                count = await page.locator(selector).count()
                if count > 0:
                    print(f"✅ Found {count} course element(s) with selector: {selector}")
                    courses_found.append(selector)
            
            # Step 6: Test Assignments page
            print("\n📝 Step 6: Testing Assignments page...")
            
            assignments_clicked = False
            for link_info in found_links:
                if "assignment" in link_info["keyword"].lower() or "homework" in link_info["keyword"].lower():
                    try:
                        print(f"Clicking on: {link_info['text']}")
                        await page.click(f"a:has-text('{link_info['text']}')")
                        await page.wait_for_load_state("networkidle")
                        await page.screenshot(path="assignments_page.png")
                        print("📸 Screenshot saved: assignments_page.png")
                        assignments_clicked = True
                        break
                    except:
                        continue
            
            if not assignments_clicked:
                print("⚠️ Could not find assignments link, trying common URLs...")
                assignment_urls = [
                    f"{PORTAL_BASE_URL}/assignments",
                    f"{PORTAL_BASE_URL}/homework",
                    f"{PORTAL_BASE_URL}/student/assignments"
                ]
                
                for url in assignment_urls:
                    try:
                        print(f"Trying URL: {url}")
                        await page.goto(url)
                        await page.wait_for_load_state("networkidle")
                        await page.screenshot(path="assignments_page.png")
                        print("📸 Screenshot saved: assignments_page.png")
                        break
                    except:
                        continue
            
            # Step 7: Generate configuration
            print("\n⚙️ Step 7: Generating configuration...")
            
            config = {
                "grades": {
                    "url": f"{PORTAL_BASE_URL}/grades",
                    "table_selector": tables_found[0] if tables_found else "table",
                    "course_selector": courses_found[0] if courses_found else ".course-name",
                    "grade_selector": ".grade, .score, td:nth-child(2)",
                    "date_selector": ".date, .due-date, td:nth-child(3)"
                },
                "assignments": {
                    "url": f"{PORTAL_BASE_URL}/assignments",
                    "table_selector": tables_found[0] if tables_found else "table",
                    "title_selector": ".title, .assignment-name, td:nth-child(1)",
                    "course_selector": courses_found[0] if courses_found else ".course",
                    "status_selector": ".status, .assignment-status, td:nth-child(4)",
                    "due_date_selector": ".due-date, .due, td:nth-child(3)"
                }
            }
            
            # Save configuration
            import json
            with open("infinite_campus_config.json", "w") as f:
                json.dump(config, f, indent=2)
            
            print("✅ Configuration saved to: infinite_campus_config.json")
            print("\n📋 Next steps:")
            print("1. Review the screenshots to verify the page structure")
            print("2. Update the selectors in infinite_campus_config.json if needed")
            print("3. Use this configuration in your MCP server")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            print("\n⏳ Keeping browser open for 30 seconds so you can inspect...")
            await page.wait_for_timeout(30000)
            await browser.close()

if __name__ == "__main__":
    asyncio.run(analyze_infinite_campus())
