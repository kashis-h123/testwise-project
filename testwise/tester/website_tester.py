from playwright.sync_api import sync_playwright
import os
from urllib.parse import urlparse
from django.conf import settings
from bs4 import BeautifulSoup
from .ai_generator import generate_ai_test_cases


# ---------------------------
# DOM ANALYZER (BeautifulSoup)
# ---------------------------

def analyze_dom(html):

    soup = BeautifulSoup(html, "html.parser")

    forms = soup.find_all("form")
    buttons = soup.find_all("button")
    links = soup.find_all("a")
    images = soup.find_all("img")

    images_without_alt = []

    for img in images:
        if not img.get("alt"):
            images_without_alt.append(img.get("src"))

    return {
        "forms": len(forms),
        "buttons": len(buttons),
        "links": len(links),
        "images_without_alt": images_without_alt
    }


# ---------------------------
# MAIN WEBSITE TESTER
# ---------------------------

def test_website(url):

    report = {}

    broken_links = {}
    visited_pages = []
    images_without_alt = []
    all_ai_cases = []
    ai_error = None
    ai_called = False

    try:

        with sync_playwright() as p:

            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(url, timeout=60000)

            domain = urlparse(url).netloc

            links = page.query_selector_all("a")
            internal_links = []

            for link in links:

                href = link.get_attribute("href")

                if href and href.startswith("http") and domain in href:
                    internal_links.append(href)

            pages_to_visit = [url] + internal_links[:4]

            total_buttons = 0
            total_forms = 0
            total_links = 0

            for page_url in pages_to_visit:

                try:

                    page.goto(page_url, timeout=60000)

                    visited_pages.append(page_url)

                    html = page.content()

                    dom_report = analyze_dom(html)

                    try:
                        if not ai_called:

                            ai_cases = generate_ai_test_cases(dom_report, page.title())

                            if not ai_cases or "failed" in str(ai_cases).lower():
                                ai_error = "⚠️ AI test case generation failed. Please try again later."
                            else:
                                all_ai_cases.extend(ai_cases)

                            ai_called = True

                    except Exception as e:
                        print("AI Error:", e)
                        ai_error = "⚠️ AI test case generation failed. Please try again later."
                        ai_called = True

                    total_buttons += dom_report["buttons"]
                    total_forms += dom_report["forms"]
                    total_links += dom_report["links"]

                    images_without_alt.extend(dom_report["images_without_alt"])

                    page_links = page.query_selector_all("a")

                    page_broken = []

                    for link in page_links:
                        href = link.get_attribute("href")

                        if href and href.startswith("http"):
                            try:
                                response = page.request.get(href, timeout=10000)

                                if response.status >= 400:
                                    page_broken.append({
                                        "url": href,
                                        "status": response.status
                                    })

                            except:
                                page_broken.append({
                                    "url": href,
                                    "status": "Error"
                                })

                    # Store per page
                    broken_links[page_url] = page_broken

                except:
                    continue


            screenshot_path = os.path.join(settings.MEDIA_ROOT, "screenshot.png")

            page.goto(url)

            page.screenshot(path=screenshot_path, full_page=True)

            report["status"] = "Website Crawled Successfully"
            report["title"] = page.title()

            report["visited_pages"] = visited_pages

            report["total_buttons"] = total_buttons
            report["total_forms"] = total_forms
            report["total_links"] = total_links

            report["broken_links"] = broken_links
            report["broken_count"] = sum(len(v) for v in broken_links.values())

            report["ai_test_cases"] = all_ai_cases
            report["ai_error"] = ai_error

            report["images_without_alt"] = images_without_alt

            report["screenshot"] = settings.MEDIA_URL + "screenshot.png"

            browser.close()

    except Exception as e:

        report["status"] = "Error loading website"
        report["error"] = str(e)

    return report