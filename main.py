'''
    main python file containing all the user interface aspects of the program
'''
from selenium import webdriver

#import matplotlib.pyplot as pty
from web_scraper.WebReader import webReader as wr

#make functionality to provide the hyperlink and the attribute to search for

# Option 1: Scrape links from category page (collects all injury report URLs)
# URL = 'https://racerxonline.com/category/injury-report'
# wr.mainPageReader(URL)

# Option 2: Scrape injury data from all URLs in link_list.txt
wr.scrapeInjuryData()