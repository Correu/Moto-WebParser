'''
    file reader class, contains methods to get contents from the file. test test 
'''

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

class webReader:

    #selenium main page reader
    def mainPageReader(mainPage):
        try:
            driver = webdriver.Chrome("WebDrivers/chromedriver")
            driver.get(mainPage)
            print(f'{driver.current_url}')
            testtitle = driver.title
            print(f'{testtitle}')
            #finding the links on each individual page
            links_List = []
            findLinks = driver.find_elements(By.PARTIAL_LINK_TEXT, "injury_report")
            for link in range(len(findLinks)):
                links_List.append(findLinks[link].text)
            
            test = driver.find_elements(By.TAG_NAME, "li")
            testList = []
            for i in range(len(test)):
                testList.append(test[i].text)
                print(testList[i])
            listFile = "link_list.txt"
            with open(listFile, "w") as file_object:
                for i in range(len(links_List)):
                    file_object.write(links_List[i])
        finally:
            driver.quit()