from selenium import webdriver
#from selenium.webdriver.firefox.service import Service
#from selenium.webdriver.firefox.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

# Set Firefox options
options = Options()
options.add_argument("--start-maximized")  # Open in full screen
# options.add_argument("--headless")       # Uncomment to run without opening a window

# Initialize the Firefox WebDriver
service = Service("/home/tylers-pc/Desktop/WebApps/Moto-WebParser/WebDrivers/chromedriver-linux64/chromedriver")  # Path to geckodriver
driver = webdriver.Chrome(service=service, options=options)

# Open a webpage
driver.get("https://www.google.com")

# Wait for a few seconds to observe
time.sleep(5)

# Close the browser
driver.quit()
