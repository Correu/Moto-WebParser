'''
    Data Organizer script to convert injury_list.txt to CSV format
    Extracts Rider, Injury, Track, and Date from HTML-formatted injury data
'''

import re
import csv
from html.parser import HTMLParser
from urllib.parse import urlparse
from datetime import datetime

class InjuryHTMLParser(HTMLParser):
    """Custom HTML parser to extract rider information from injury entries"""
    
    def __init__(self):
        super().__init__()
        self.rider_name = ""
        self.injury = ""
        self.status = ""
        self.in_rider_link = False
        self.rider_data = []
    
    def handle_starttag(self, tag, attrs):
        """Handle opening tags"""
        if tag == 'a':
            # Check if this is a rider link
            for attr_name, attr_value in attrs:
                if attr_name == 'class' and ('show_card' in attr_value or 'show_rider_card' in attr_value):
                    self.in_rider_link = True
                    break
    
    def handle_endtag(self, tag):
        """Handle closing tags"""
        if tag == 'a':
            self.in_rider_link = False
    
    def handle_data(self, data):
        """Handle text data"""
        if self.in_rider_link:
            self.rider_name = data.strip()
    
    def parse_injury_entry(self, html_content):
        """Parse a single injury entry HTML and extract rider, injury, status"""
        self.rider_name = ""
        self.injury = ""
        self.status = ""
        self.in_rider_link = False
        self.feed(html_content)
        
        # Extract the full text content (rider name is already extracted from link)
        # Pattern: <a>Rider Name</a> – Injury | Status
        # After removing HTML: "Rider Name – Injury | Status"
        
        # Remove HTML tags but preserve text
        text_content = re.sub(r'<[^>]+>', '', html_content)
        text_content = text_content.strip()
        
        # The format is typically: "Rider Name – Injury | Status"
        # Sometimes: "Rider Name - Injury | Status" (single dash)
        # Sometimes: "Rider Name – Injury|Status" (no space)
        
        if '|' in text_content:
            # Split by | to get status
            parts = text_content.split('|', 1)
            if len(parts) == 2:
                status = parts[1].strip()
                main_part = parts[0].strip()
                
                # Now split main_part to get rider and injury
                # Remove rider name if we already extracted it
                if self.rider_name and self.rider_name in main_part:
                    # Remove rider name from the beginning
                    injury_part = main_part.replace(self.rider_name, '', 1).strip()
                    # Remove leading dash/separator
                    injury_part = re.sub(r'^[–\-]+\s*', '', injury_part).strip()
                else:
                    # Try to extract rider name from main_part
                    if '–' in main_part:
                        name_injury = main_part.split('–', 1)
                        if not self.rider_name:
                            self.rider_name = name_injury[0].strip()
                        injury_part = name_injury[1].strip() if len(name_injury) > 1 else ""
                    elif ' - ' in main_part:
                        name_injury = main_part.split(' - ', 1)
                        if not self.rider_name:
                            self.rider_name = name_injury[0].strip()
                        injury_part = name_injury[1].strip() if len(name_injury) > 1 else ""
                    else:
                        # Single dash
                        name_injury = main_part.split('-', 1)
                        if not self.rider_name and len(name_injury) > 0:
                            # Check if first part looks like a name (not too long)
                            first_part = name_injury[0].strip()
                            if len(first_part.split()) <= 3:
                                self.rider_name = first_part
                                injury_part = name_injury[1].strip() if len(name_injury) > 1 else ""
                            else:
                                injury_part = main_part
                        else:
                            injury_part = name_injury[1].strip() if len(name_injury) > 1 else ""
                
                self.injury = injury_part
                self.status = status
            else:
                # Malformed, try to extract what we can
                self.injury = text_content
                self.status = ""
        else:
            # No status marker
            if self.rider_name and self.rider_name in text_content:
                injury_part = text_content.replace(self.rider_name, '', 1).strip()
                injury_part = re.sub(r'^[–\-]+\s*', '', injury_part).strip()
                self.injury = injury_part
            elif '–' in text_content:
                parts = text_content.split('–', 1)
                if not self.rider_name:
                    self.rider_name = parts[0].strip()
                self.injury = parts[1].strip() if len(parts) > 1 else ""
            elif ' - ' in text_content:
                parts = text_content.split(' - ', 1)
                if not self.rider_name:
                    self.rider_name = parts[0].strip()
                self.injury = parts[1].strip() if len(parts) > 1 else ""
            else:
                if not self.rider_name:
                    # Try to guess rider name (first few words)
                    words = text_content.split()
                    if words:
                        self.rider_name = ' '.join(words[:2]) if len(words) >= 2 else words[0]
                        self.injury = ' '.join(words[2:]) if len(words) > 2 else ""
                    else:
                        self.injury = text_content
                else:
                    self.injury = text_content
        
        return {
            'rider': self.rider_name.strip(),
            'injury': self.injury.strip(),
            'status': self.status.strip()
        }


def extract_date_from_url(url):
    """Extract date from URL in format YYYY/MM/DD"""
    try:
        # Pattern: https://racerxonline.com/YYYY/MM/DD/...
        match = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', url)
        if match:
            year, month, day = match.groups()
            # Format as YYYY-MM-DD for CSV
            return f"{year}-{month}-{day}"
    except:
        pass
    return ""


def parse_injury_list(input_file="injury_list.txt", output_file="injury_data.csv"):
    """
    Parse injury_list.txt and convert to CSV format
    """
    parser = InjuryHTMLParser()
    injury_records = []
    current_track = ""
    current_url = ""
    current_date = ""
    
    try:
        with open(input_file, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                
                # Check for track information comment
                if line.startswith("<!--") and "TRACK:" in line:
                    # Extract track name and URL from comment
                    # Format: <!-- TRACK: Track Name | URL: https://... -->
                    track_match = re.search(r'TRACK:\s*([^|]+)', line)
                    url_match = re.search(r'URL:\s*(https?://[^\s>]+)', line)
                    
                    if track_match:
                        current_track = track_match.group(1).strip()
                    if url_match:
                        current_url = url_match.group(1).strip()
                        current_date = extract_date_from_url(current_url)
                
                # Check for injury entry (heading tags with rider links)
                elif line.startswith("<h") and ("show_card" in line or "show_rider_card" in line):
                    # Skip header/title h1 tags that are not rider entries
                    if 'class="text-xl' in line or 'Injury Report' in line:
                        continue
                    
                    # Parse the injury entry
                    rider_data = parser.parse_injury_entry(line)
                    
                    if rider_data['rider']:  # Only add if we found a rider name
                        injury_records.append({
                            'Rider': rider_data['rider'],
                            'Injury': rider_data['injury'],
                            'Track': current_track,
                            'Date': current_date
                        })
    
    except FileNotFoundError:
        print(f"Error: {input_file} not found!")
        return
    except Exception as e:
        print(f"Error reading file: {e}")
        return
    
    # Write to CSV
    if injury_records:
        try:
            with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
                fieldnames = ['Rider', 'Injury', 'Track', 'Date']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for record in injury_records:
                    writer.writerow(record)
            
            print(f"Successfully converted {len(injury_records)} injury records to {output_file}")
            print(f"CSV file contains columns: {', '.join(fieldnames)}")
            
            # Print summary statistics
            unique_riders = len(set(r['Rider'] for r in injury_records))
            unique_tracks = len(set(r['Track'] for r in injury_records if r['Track']))
            print(f"Summary: {unique_riders} unique riders, {unique_tracks} unique tracks")
            
        except Exception as e:
            print(f"Error writing CSV file: {e}")
    else:
        print("No injury records found to convert.")


if __name__ == "__main__":
    print("Starting data organization...")
    parse_injury_list()
    print("Done!")

