Goal: parse crash and injury information across action sports and visualize it in a Dash app.

This project currently supports:
- motocross / supercross (Racer X injury reports)
- off-road action motorsports starter source (Off Road Xtreme search-driven links)
- freestyle motocross source path (Swap Moto Live, keyword-based)
- BMX source path (Vital BMX, keyword-based)

UI stack:
- Plotly Dash (not Flask)

Data model (CSV):
- Sport
- Discipline
- Athlete
- Rider (legacy compatibility)
- Injury
- Venue
- Track (legacy compatibility)
- Date

Candidate action-sports sources:
- https://racerxonline.com/category/injury-report
- https://www.swapmotolive.com/?s=injury
- https://www.offroadxtreme.com/?s=crash
- https://www.vitalbmx.com/ (search injury/crash related tags)
- https://www.thrashermagazine.com/ (news features, less structured injury indexing)

Legal/scraping caveats:
- Check each site's robots.txt and terms before scraping.
- Respect rate limits and avoid aggressive crawling.
- Prefer category pages, tagged archives, and search pages for seed URLs.

Documentation:
- requests: https://pypi.org/project/requests/
- selenium: https://www.selenium.dev/documentation/en/

WebDrivers:
- ChromeDriver: https://developer.chrome.com/docs/chromedriver/downloads
- GeckoDriver: https://geckodriver.com/

Running the scripts

1) Create and activate a virtual environment:
1. python3 -m venv <venv-name>
2. source <venv-name>/bin/activate

2) Collect links for a source:
- Motocross (default): call webReader.mainPageReader()
- Off-road: call webReader.mainPageReader(source_id="offroadxtreme")
- FMX: call webReader.mainPageReader(source_id="swapmoto")
- BMX: call webReader.mainPageReader(source_id="vitalbmx")

3) Scrape article/entry content:
- Motocross: webReader.scrapeInjuryData(source_id="racerx")
- Off-road: webReader.scrapeInjuryData(source_id="offroadxtreme")
- FMX: webReader.scrapeInjuryData(source_id="swapmoto")
- BMX: webReader.scrapeInjuryData(source_id="vitalbmx")
- All configured sources:
  - webReader.scrapeAllConfiguredSources()

4) Build CSV files (recommended one step):
- python3 build_updated_data.py
  This will:
  - Discover all injury_list_*.txt plus injury_list.txt (if present), merge -> injury_data.csv
  - Cleanse and dedupe (normalized keys, standardized Sport/Athlete/Injury/Venue/Date) -> updated_data.csv

  Cleansing rules (see helpers/helpers.py):
  - Sport: mapped to canonical codes (motocross, off_road, bmx, skate, fmx, etc.)
  - Athlete/Rider and Venue/Track: stripped, whitespace collapsed, title case for display
  - Injury: whitespace collapsed; short ALL CAPS phrases title-cased with common acronyms kept (ACL, MCL, …)
  - Date: normalized to YYYY-MM-DD when parseable
  - Duplicates removed using case-insensitive keys on sport + athlete + injury + venue
  - When duplicates exist, the earliest valid Date is kept

  Manual / split steps:
- python3 DataOrganizer.py   (merge discovered lists -> injury_data.csv only)
- python3 -c "from helpers.helpers import parse_injury_data_first_occurrence; parse_injury_data_first_occurrence()"

5) Start the Dash app:
- python3 main.py

Date caveat:
- Rows with no parseable Date are still written to updated_data.csv but the Dash app drops them when loading (invalid/missing dates). Off-road/blog URLs without /YYYY/MM/DD/ may need a future parser improvement (article meta/time tags).

