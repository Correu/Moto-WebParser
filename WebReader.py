'''
    file reader class, contains methods to get contents from the file. test test 
'''

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
#from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

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
            print(f'{driver.current_url}')
            print(driver.title)
            #finding the links on each individual page
            links_List = []
            findLinks = driver.find_elements(By.PARTIAL_LINK_TEXT, "Injury Report")
            links = driver.find_elements(By.CSS_SELECTOR, ".ui_link.big_link")
            #find the next attribute/link to navigate to the next page and do the loop and append to the list again

            #adding links to the links_List collection
            for link in links:
                print(link.get_attribute("href"))
                links_List.append(link.get_attribute("href"))

            #Writing the list to the file link_list.txt
            listFile = "link_list.txt"
            with open(listFile, "w") as file_object:
                for i in range(len(links_List)):
                    file_object.write(links_List[i] + "\n")
            
        finally:
            driver.quit()
        