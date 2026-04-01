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

4) Build CSV files:
- python3 DataOrganizer.py
- python3 helpers/helpers.py
- Optional merge from multiple source files:
  - from DataOrganizer import parse_multiple_injury_lists
  - parse_multiple_injury_lists([
      "injury_list_racerx.txt",
      "injury_list_offroadxtreme.txt",
      "injury_list_swapmoto.txt",
      "injury_list_vitalbmx.txt"
    ], output_file="injury_data.csv")

5) Start the Dash app:
- python3 main.py

