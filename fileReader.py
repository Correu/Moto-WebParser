'''
    file reader class, contains methods to get contents from the file. test test 
'''

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

class fileReader:

    #replacing beautiful soup with selenium
    def seleReader(mainPage):
        driver = webdriver.Chrome("WebDrivers/chromedriver")
        driver.get(mainPage)
        print(f'{driver.current_url}')
       # test = driver.find_element(with_tag_name())
        testtitle = driver.title
        #test = driver.find_element_by_id("ui_big")
        print(f'{testtitle}')
        driver.quit()