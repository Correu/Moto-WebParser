'''
    file reader class, contains methods to get contents from the file. test test 
'''

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
#from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from urllib.parse import urljoin
import time
import re

class webReader:

    #selenium main page reader
    def mainPageReader(mainPage):

        # Set Chrome options
        options = Options()
        options.add_argument("--start-maximized")  # Open in full screen
        # options.add_argument("--headless")       # Uncomment to run without opening a window

        # Initialize the Chrome WebDriver
        service = Service("/home/tylers-pc/Desktop/WebApps/Moto-WebParser/WebDrivers/chromedriver-linux64/chromedriver")  # Path to chromedriver
        driver = webdriver.Chrome(service=service, options=options)

        #driverService = Service('WebDrivers/geckodriver') 
        #options = FirefoxOptions()
        #options.binary_location = r"/usr/bin/firefox"
        #driver = webdriver.Firefox(options=options)
        try:
            driver.get(mainPage)
            print(f'Starting URL: {driver.current_url}')
            print(f'Page Title: {driver.title}')
            
            # Initialize the links list to collect from all pages
            links_List = []
            page_num = 1
            
            # Loop through all pages until no more "next" button is found
            while True:
                print(f"\n--- Processing Page {page_num} ---")
                
                # Wait for page to load
                time.sleep(2)  # Give the page time to fully render
                
                # Find links containing "Injury report" on current page
                # Using XPath to find links containing "Injury report" text (case-insensitive)
                xpath_query = "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'injury report')]"
                links = driver.find_elements(By.XPATH, xpath_query)
                
                # Alternative fallback: Find all links and filter by text content
                if len(links) == 0:
                    all_links = driver.find_elements(By.TAG_NAME, "a")
                    for link in all_links:
                        link_text = link.text.lower()
                        if "injury report" in link_text:
                            links.append(link)
                
                print(f"Found {len(links)} links containing 'Injury report' on page {page_num}")
                
                # Add links from current page to the master list
                base_url = driver.current_url
                for link in links:
                    href = link.get_attribute("href")
                    if href:
                        # Convert relative URLs to absolute URLs using urljoin
                        absolute_url = urljoin(base_url, href)
                        
                        # Filter out invalid URLs and fragments, avoid duplicates
                        if absolute_url.startswith('http') and absolute_url not in links_List:
                            print(f"  - {absolute_url}")
                            links_List.append(absolute_url)
                
                print(f"Total links collected so far: {len(links_List)}")
                
                # Try to find the "next" button/link
                next_button = None
                
                # Strategy 1: Look for link/button with text containing "next" (case-insensitive)
                next_selectors = [
                    ("xpath", "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'next')]"),
                    ("xpath", "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'next')]"),
                    ("xpath", "//a[@aria-label='Next' or @aria-label='next' or @aria-label='Next Page']"),
                    ("xpath", "//a[contains(@class, 'next') or contains(@class, 'pagination')]"),
                    ("xpath", "//a[contains(@href, 'page=')]"),  # Links with page parameter
                ]
                
                for selector_type, selector in next_selectors:
                    try:
                        if selector_type == "xpath":
                            elements = driver.find_elements(By.XPATH, selector)
                            # Filter to find the actual "next" link (not previous, not current page)
                            for elem in elements:
                                text = elem.text.lower()
                                href = elem.get_attribute("href") or ""
                                # Check if it's actually a "next" link
                                if ("next" in text or "→" in text or "»" in text) and \
                                   ("prev" not in text and "previous" not in text):
                                    next_button = elem
                                    break
                                # Or check if href contains page number increment
                                elif "page=" in href:
                                    try:
                                        # Check if this is a next page (page number higher than current)
                                        current_url = driver.current_url
                                        if "page=" in current_url:
                                            current_page = int(current_url.split("page=")[1].split("&")[0])
                                            next_page = int(href.split("page=")[1].split("&")[0])
                                            if next_page > current_page:
                                                next_button = elem
                                                break
                                    except:
                                        pass
                        if next_button:
                            break
                    except Exception as e:
                        continue
                
                # Strategy 2: Look for pagination structure (common patterns)
                if not next_button:
                    try:
                        # Look for pagination container and find next link
                        pagination = driver.find_elements(By.CSS_SELECTOR, ".pagination a, .pager a, [class*='pagination'] a, [class*='pager'] a")
                        for link in pagination:
                            text = link.text.lower().strip()
                            if text in ["next", "→", "»", "next page"]:
                                next_button = link
                                break
                    except:
                        pass
                
                # If next button found, click it and continue
                if next_button:
                    try:
                        next_url = next_button.get_attribute("href")
                        if next_url:
                            print(f"Found next button. Navigating to: {next_url}")
                            # Scroll to the button to ensure it's visible
                            driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                            time.sleep(1)
                            
                            # Click the next button
                            driver.execute_script("arguments[0].click();", next_button)
                            
                            # Wait for new page to load
                            WebDriverWait(driver, 10).until(
                                lambda d: d.current_url != base_url
                            )
                            time.sleep(2)  # Additional wait for content to load
                            page_num += 1
                            continue
                    except Exception as e:
                        print(f"Error clicking next button: {e}")
                        break
                else:
                    # No next button found, we've reached the end
                    print("\nNo 'next' button found. Reached the end of pagination.")
                    break
            
            # Writing all collected links to the file
            print(f"\n=== Final Summary ===")
            print(f"Total pages processed: {page_num}")
            print(f"Total unique links found: {len(links_List)}")
            
            listFile = "link_list.txt"
            with open(listFile, "w") as file_object:
                for i in range(len(links_List)):
                    file_object.write(links_List[i] + "\n")
            
            print(f"Links saved to {listFile}")
            
        finally:
            driver.quit()
    
    # Method to scrape injury data from each URL in link_list.txt
    def scrapeInjuryData(linkFile="link_list.txt", outputFile="injury_list.txt"):
        """
        Reads URLs from link_list.txt, visits each page, and extracts rider injury information.
        Saves the extracted data to injury_list.txt.
        """
        # Set Chrome options
        options = Options()
        options.add_argument("--start-maximized")  # Open in full screen
        # options.add_argument("--headless")       # Uncomment to run without opening a window

        # Initialize the Chrome WebDriver
        service = Service("/home/tylers-pc/Desktop/WebApps/Moto-WebParser/WebDrivers/chromedriver-linux64/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)
        
        try:
            # Read URLs from link_list.txt
            try:
                with open(linkFile, "r") as file:
                    urls = [line.strip() for line in file.readlines() if line.strip()]
            except FileNotFoundError:
                print(f"Error: {linkFile} not found!")
                return
            
            # Filter out category pages (these are pagination links, not actual injury report pages)
            injury_urls = [url for url in urls if "/category/injury-report/" not in url]
            
            print(f"Total URLs in file: {len(urls)}")
            print(f"Valid injury report URLs: {len(injury_urls)}")
            print(f"Filtered out {len(urls) - len(injury_urls)} category/pagination pages\n")
            
            all_injury_data = []
            
            # Process each URL
            for idx, url in enumerate(injury_urls, 1):
                try:
                    print(f"[{idx}/{len(injury_urls)}] Processing: {url}")
                    
                    # Extract track name from URL
                    track_name = ""
                    try:
                        # Extract the last meaningful part of URL (after last slash)
                        url_parts = url.rstrip("/").split("/")
                        slug = url_parts[-1] if url_parts else ""
                        
                        if slug:
                            # Pattern 1: {track}-injury-report-{details}
                            # Example: "budds-creek-injury-report-haarup-mosiman-out"
                            if "-injury-report" in slug:
                                track_part = slug.split("-injury-report")[0]
                                if track_part:
                                    track_name = track_part.replace("-", " ").title()
                            
                            # Pattern 2: injury-report-{track} or injury-report-for-{track}
                            # Example: "injury-report-unadilla" or "injury-report-for-unadilla"
                            elif slug.startswith("injury-report"):
                                if slug.startswith("injury-report-for-"):
                                    track_part = slug.replace("injury-report-for-", "")
                                else:
                                    track_part = slug.replace("injury-report-", "")
                                
                                if track_part:
                                    # Handle special cases like SMX
                                    if "smx" in track_part.lower():
                                        if "round" in track_part.lower():
                                            track_name = "SMX Playoffs"
                                        elif "world-championship" in track_part.lower() or "final" in track_part.lower():
                                            track_name = "SMX World Championship Final"
                                        else:
                                            track_name = "SMX"
                                    else:
                                        # Regular track - clean it up
                                        # Remove rider names and other details (usually everything after first 2-3 words)
                                        track_parts = track_part.split("-")
                                        # Take first 1-3 meaningful parts as track name
                                        filtered_parts = []
                                        skip_words = ["injury", "report", "for", "at", "the", "and", "more", "return"]
                                        for part in track_parts[:5]:  # Limit to first 5 parts
                                            if part.lower() not in skip_words and len(part) > 2:
                                                filtered_parts.append(part)
                                                if len(filtered_parts) >= 3:  # Usually track name is 1-3 words
                                                    break
                                        if filtered_parts:
                                            track_name = " ".join(filtered_parts).title()
                            
                            # Pattern 3: Just track name (fallback)
                            elif not track_name:
                                # Remove common suffixes and clean
                                track_parts = slug.split("-")
                                filtered_parts = [p for p in track_parts[:4] if p.lower() not in ["injury", "report", "for"]]
                                if filtered_parts:
                                    track_name = " ".join(filtered_parts).title()
                    except Exception as e:
                        pass
                    
                    # Navigate to the page
                    driver.get(url)
                    time.sleep(2)  # Wait for page to load
                    
                    # Try to get track name from page title if not found in URL
                    if not track_name or len(track_name) < 3:
                        try:
                            page_title = driver.title
                            # Try to extract track from title (often format: "Injury Report: Track Name" or "Track Name Injury Report")
                            if "injury report" in page_title.lower():
                                title_parts = page_title.split("Injury Report")
                                if len(title_parts) > 1:
                                    potential_track = title_parts[-1].strip(": -").strip()
                                    if potential_track and len(potential_track) > 3:
                                        track_name = potential_track
                        except:
                            pass
                    
                    # Try to get track from h1 or article title if still not found
                    if not track_name or len(track_name) < 3:
                        try:
                            # Look for main heading that might contain track name
                            main_heading = driver.find_elements(By.XPATH, "//h1 | //article//h1 | //header//h1")
                            for h1 in main_heading[:1]:  # Just check first h1
                                text = h1.text.strip()
                                if text and "injury" not in text.lower() and len(text) < 50:
                                    track_name = text
                                    break
                        except:
                            pass
                    
                    # Clean up track name
                    track_name = track_name.strip() if track_name else "Unknown Track"
                    print(f"  Track: {track_name}")
                    
                    # Find all heading elements (h1-h4) that contain rider injury information
                    # These typically have links with class "show_card" inside them, or contain rider names
                    # Try multiple XPath strategies to find injury entries
                    injury_elements = []
                    
                    # Strategy 1: Find headings with show_card links (common pattern)
                    injury_elements.extend(driver.find_elements(By.XPATH, "//h1[.//a[@class='show_card']]"))
                    injury_elements.extend(driver.find_elements(By.XPATH, "//h2[.//a[@class='show_card']]"))
                    injury_elements.extend(driver.find_elements(By.XPATH, "//h3[.//a[@class='show_card']]"))
                    injury_elements.extend(driver.find_elements(By.XPATH, "//h4[.//a[@class='show_card']]"))
                    
                    # Strategy 2: Find headings that contain rider information patterns (injury keywords + status)
                    # Look for headings that contain injury status indicators
                    all_headings = driver.find_elements(By.XPATH, "//h1 | //h2 | //h3 | //h4")
                    for heading in all_headings:
                        try:
                            text = heading.text.strip().lower()
                            # Check if it looks like an injury entry (contains status and possible injury terms)
                            if text and len(text) > 10:
                                has_status = any(status in text for status in ["| out", "| in", "| tbd", "out", "in", "tbd"])
                                has_rider_link = len(heading.find_elements(By.XPATH, ".//a")) > 0
                                # If it has status and a link, or contains common injury-related patterns
                                if has_status and (has_rider_link or any(word in text for word in ["shoulder", "knee", "arm", "wrist", "ankle", "back", "collarbone", "head", "hand", "hip", "ribs", "leg"])):
                                    if heading not in injury_elements:
                                        injury_elements.append(heading)
                        except:
                            continue
                    
                    page_injuries = []
                    seen_entries = set()  # Track seen entries to avoid duplicates
                    
                    for elem in injury_elements:
                        try:
                            # Get the HTML content of the element
                            html_content = elem.get_attribute('outerHTML')
                            if html_content:
                                # Filter out non-injury entries (like "Motocross & Supercross News")
                                text = elem.text.strip()
                                # Check if this is a valid injury entry
                                if text and len(text) > 10:
                                    # Filter out common non-injury headings
                                    text_lower = text.lower()
                                    if ("motocross & supercross news" not in text_lower and
                                        "racer x online" not in text_lower and
                                        not text_lower.startswith("motocross") and
                                        ("out" in text_lower or "in" in text_lower or "tbd" in text_lower)):
                                        
                                        # Create a simple text-based hash to detect duplicates
                                        text_hash = hash(text)
                                        if text_hash not in seen_entries:
                                            seen_entries.add(text_hash)
                                            page_injuries.append(html_content)
                        except Exception as e:
                            continue
                    
                    if page_injuries:
                        print(f"  Found {len(page_injuries)} injury entries")
                        # Add track information header before this page's injuries
                        track_header = f"<!-- TRACK: {track_name} | URL: {url} -->"
                        all_injury_data.append(track_header)
                        all_injury_data.extend(page_injuries)
                    else:
                        print(f"  No injury data found on this page")
                        # Still record track even if no injuries found
                        track_header = f"<!-- TRACK: {track_name} | URL: {url} | NO INJURIES -->"
                        all_injury_data.append(track_header)
                        
                except Exception as e:
                    print(f"  Error processing {url}: {e}")
                    continue
            
            # Write all collected injury data to output file
            print(f"\n=== Final Summary ===")
            print(f"Total pages processed: {len(injury_urls)}")
            print(f"Total injury entries collected: {len(all_injury_data)}")
            
            with open(outputFile, "w", encoding="utf-8") as file:
                for injury_entry in all_injury_data:
                    file.write(injury_entry + "\n")
            
            print(f"Injury data saved to {outputFile}")
            
        finally:
            driver.quit()
        