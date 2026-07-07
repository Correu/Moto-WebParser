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
import os
import time
import re

class webReader:
    @staticmethod
    def _data_path(filename):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(root, "data")
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, filename)

    SOURCE_CONFIGS = {
        "racerx": {
            "sport": "motocross",
            "discipline": "supercross/motocross",
            "seed_url": "https://racerxonline.com/category/injury-report",
            "include_keywords": ["injury report"],
            "exclude_url_patterns": ["/category/injury-report/"],
            "link_file": "link_list.txt",
        },
        "offroadxtreme": {
            "sport": "off_road",
            "discipline": "trophy_truck/desert",
            "seed_url": "https://www.offroadxtreme.com/?s=crash",
            "include_keywords": [
                "crash", "roll", "rolled", "injury", "hospital", "wreck", "accident",
                "baja", "score", "trophy truck"
            ],
            "exclude_url_patterns": ["/tag/", "/category/", "/author/", "/page/"],
            "link_file": "link_list_offroad.txt",
        },
        "swapmoto": {
            "sport": "motocross",
            "discipline": "freestyle_motocross",
            "seed_url": "https://www.swapmotolive.com/?s=injury",
            "include_keywords": ["injury", "crash", "out", "hospital", "return"],
            "exclude_url_patterns": ["/page/", "/author/", "/category/"],
            "link_file": "link_list_swapmoto.txt",
        },
        "vitalbmx": {
            "sport": "bmx",
            "discipline": "park/street/dirt",
            "seed_url": "https://www.vitalbmx.com/search?query=injury",
            "include_keywords": ["injury", "crash", "hospital", "out", "accident", "slam"],
            "exclude_url_patterns": ["/forum/", "/photos/", "/videos/", "/members/"],
            "link_file": "link_list_vitalbmx.txt",
        },
    }
    INCIDENT_KEYWORDS = [
        "injury", "injured", "crash", "wreck", "roll", "rolled",
        "hospital", "concussion", "fracture", "broken", "out for", "ruled out"
    ]

    @staticmethod
    def get_source_config(source_id):
        """Return source configuration with Racer X as safe default."""
        return webReader.SOURCE_CONFIGS.get(source_id, webReader.SOURCE_CONFIGS["racerx"])

    @staticmethod
    def _is_candidate_link(link_text, href, keywords):
        text = (link_text or "").lower()
        url = (href or "").lower()
        combined = f"{text} {url}"
        return any(keyword in combined for keyword in keywords)

    @staticmethod
    def _build_track_header(track_name, url, sport, discipline, no_injuries=False):
        base = f"<!-- SPORT: {sport} | DISCIPLINE: {discipline} | TRACK: {track_name} | URL: {url}"
        if no_injuries:
            return base + " | NO INJURIES -->"
        return base + " -->"

    @staticmethod
    def _create_chrome_driver(options):
        """
        Create a Chrome WebDriver.
        Tries Selenium Manager first (auto-matching local Chrome),
        then falls back to the project-pinned chromedriver path.
        """
        try:
            return webdriver.Chrome(options=options)
        except Exception as first_error:
            print(f"Selenium Manager driver init failed, trying local chromedriver: {first_error}")
            service = Service("/home/tylers-pc/Desktop/WebApps/Moto-WebParser/WebDrivers/chromedriver-linux64/chromedriver")
            return webdriver.Chrome(service=service, options=options)

    @staticmethod
    def _extract_generic_incidents(driver):
        """
        Extract incident lines for sites without structured injury tables.
        Returns pipe-delimited rows consumed by DataOrganizer:
        ###INCIDENT###|Athlete|Injury text
        """
        incidents = []
        try:
            page_title = (driver.title or "").strip()
        except Exception:
            page_title = ""

        athlete = "Unknown Athlete"
        if page_title:
            # Simple heuristic: "Name ... crash" titles usually start with athlete name.
            candidate = re.split(r'[-|:]', page_title)[0].strip()
            if 1 <= len(candidate.split()) <= 4 and len(candidate) <= 50:
                athlete = candidate

        paragraphs = driver.find_elements(By.XPATH, "//article//p | //main//p | //p")
        seen = set()
        for p in paragraphs[:80]:
            text = p.text.strip()
            if len(text) < 30:
                continue
            lower_text = text.lower()
            if not any(keyword in lower_text for keyword in webReader.INCIDENT_KEYWORDS):
                continue
            normalized = re.sub(r'\s+', ' ', text)
            if normalized in seen:
                continue
            seen.add(normalized)
            incidents.append(f"###INCIDENT###|{athlete}|{normalized}")
            if len(incidents) >= 6:
                break

        return incidents

    #selenium main page reader
    def mainPageReader(mainPage=None, source_id="racerx"):
        source_cfg = webReader.get_source_config(source_id)
        if not mainPage:
            mainPage = source_cfg["seed_url"]

        # Set Chrome options
        options = Options()
        options.add_argument("--start-maximized")  # Open in full screen
        # options.add_argument("--headless")       # Uncomment to run without opening a window

        # Initialize the Chrome WebDriver
        driver = webReader._create_chrome_driver(options)

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
                # Source-driven link discovery for multi-sport crawling
                links = []
                all_links = driver.find_elements(By.TAG_NAME, "a")
                include_keywords = source_cfg["include_keywords"]
                for link in all_links:
                    link_text = link.text
                    href = link.get_attribute("href")
                    if not href:
                        continue
                    if webReader._is_candidate_link(link_text, href, include_keywords):
                        links.append(link)

                print(f"Found {len(links)} candidate links on page {page_num}")
                
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
            
            listFile = webReader._data_path(source_cfg["link_file"])
            with open(listFile, "w") as file_object:
                for i in range(len(links_List)):
                    file_object.write(links_List[i] + "\n")
            
            print(f"Links saved to {listFile}")
            
        finally:
            driver.quit()
    
    # Method to scrape injury data from each URL in link_list.txt
    def scrapeInjuryData(linkFile=None, outputFile=None, source_id="racerx"):
        """
        Reads URLs from a per-source link list, visits each page, and extracts injury information.
        Saves the extracted data to a per-source injury list under data/.
        """
        source_cfg = webReader.get_source_config(source_id)
        if not linkFile:
            linkFile = webReader._data_path(source_cfg["link_file"])
        elif not os.path.isabs(linkFile):
            linkFile = webReader._data_path(linkFile)

        if outputFile is None:
            outputFile = webReader._data_path(f"injury_list_{source_id}.txt")
        elif not os.path.isabs(outputFile):
            outputFile = webReader._data_path(outputFile)

        # Set Chrome options
        options = Options()
        options.add_argument("--start-maximized")  # Open in full screen
        # options.add_argument("--headless")       # Uncomment to run without opening a window

        # Initialize the Chrome WebDriver
        driver = webReader._create_chrome_driver(options)
        
        try:
            # Read URLs from link_list.txt
            try:
                with open(linkFile, "r") as file:
                    urls = [line.strip() for line in file.readlines() if line.strip()]
            except FileNotFoundError:
                print(f"Error: {linkFile} not found!")
                return
            
            # Filter out category/list pages (not actual incident report pages)
            injury_urls = []
            for url in urls:
                if any(pattern in url for pattern in source_cfg["exclude_url_patterns"]):
                    continue
                injury_urls.append(url)
            
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
                    
                    page_injuries = []
                    if source_id == "racerx":
                        # Racer X structured injury table parsing
                        injury_elements = []
                        injury_elements.extend(driver.find_elements(By.XPATH, "//h1[.//a[@class='show_card']]"))
                        injury_elements.extend(driver.find_elements(By.XPATH, "//h2[.//a[@class='show_card']]"))
                        injury_elements.extend(driver.find_elements(By.XPATH, "//h3[.//a[@class='show_card']]"))
                        injury_elements.extend(driver.find_elements(By.XPATH, "//h4[.//a[@class='show_card']]"))

                        all_headings = driver.find_elements(By.XPATH, "//h1 | //h2 | //h3 | //h4")
                        for heading in all_headings:
                            try:
                                text = heading.text.strip().lower()
                                if text and len(text) > 10:
                                    has_status = any(status in text for status in ["| out", "| in", "| tbd", "out", "in", "tbd"])
                                    has_rider_link = len(heading.find_elements(By.XPATH, ".//a")) > 0
                                    if has_status and (has_rider_link or any(word in text for word in ["shoulder", "knee", "arm", "wrist", "ankle", "back", "collarbone", "head", "hand", "hip", "ribs", "leg"])):
                                        if heading not in injury_elements:
                                            injury_elements.append(heading)
                            except Exception:
                                continue

                        seen_entries = set()
                        for elem in injury_elements:
                            try:
                                html_content = elem.get_attribute('outerHTML')
                                if not html_content:
                                    continue
                                text = elem.text.strip()
                                if text and len(text) > 10:
                                    text_lower = text.lower()
                                    if ("motocross & supercross news" not in text_lower and
                                        "racer x online" not in text_lower and
                                        not text_lower.startswith("motocross") and
                                        ("out" in text_lower or "in" in text_lower or "tbd" in text_lower)):
                                        text_hash = hash(text)
                                        if text_hash not in seen_entries:
                                            seen_entries.add(text_hash)
                                            page_injuries.append(html_content)
                            except Exception:
                                continue
                    else:
                        # Generic extraction for action-sport blogs without injury tables
                        page_injuries = webReader._extract_generic_incidents(driver)
                    
                    if page_injuries:
                        print(f"  Found {len(page_injuries)} injury entries")
                        # Add track information header before this page's injuries
                        track_header = webReader._build_track_header(
                            track_name,
                            url,
                            source_cfg["sport"],
                            source_cfg["discipline"],
                            no_injuries=False
                        )
                        all_injury_data.append(track_header)
                        all_injury_data.extend(page_injuries)
                    else:
                        print(f"  No injury data found on this page")
                        # Still record track even if no injuries found
                        track_header = webReader._build_track_header(
                            track_name,
                            url,
                            source_cfg["sport"],
                            source_cfg["discipline"],
                            no_injuries=True
                        )
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

    @staticmethod
    def scrapeAllConfiguredSources():
        """
        Convenience wrapper that crawls and scrapes all configured sources.
        Output files are named injury_list_<source_id>.txt.
        """
        for source_id in webReader.SOURCE_CONFIGS:
            print(f"\n=== Processing source: {source_id} ===")
            webReader.mainPageReader(source_id=source_id)
            output_file = webReader._data_path(f"injury_list_{source_id}.txt")
            webReader.scrapeInjuryData(source_id=source_id, outputFile=output_file)