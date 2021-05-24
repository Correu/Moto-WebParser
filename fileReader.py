'''
    file reader class, contains methods to get contents from the file. test test 
'''

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

class fileReader:

    #replacing beautiful soup with selenium
    def seleReader(mainPage):
        try:
            driver = webdriver.Chrome("WebDrivers/chromedriver")
            driver.get(mainPage)
            print(f'{driver.current_url}')
            testtitle = driver.title
            print(f'{testtitle}')
            test = driver.find_element_by_class_name("s_100")
            print(f'{test}')
        finally:
            driver.quit()