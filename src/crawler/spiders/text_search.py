import os
from selenium import webdriver
import sys
import time

PRINT_TO_CONSOLE = False
SCROLL_NUMBER = 3

class TextSearch(object):
    def __init__(self, protected_phrases, webdriver_path):
        self.protected_phrases = protected_phrases
        sys.path.insert(0, webdriver_path)
        sys.path.append(webdriver_path)
        os.environ["PATH"] += os.pathsep + webdriver_path

    def search_for_protected_phrases(self, websites):
        driver = webdriver.PhantomJS()
        found_websites_list = []
        for website in websites:
            try:
                html_content = self.get_website_html_string_with_webdriver(driver, website)
                for phrase in self.protected_phrases:
                    if phrase in html_content:
                        found_string = "Phrase \"{phrase}\" found in website: {site}".format(phrase=phrase, site=str(website))
                        found_websites_list.append(found_string)
                        if PRINT_TO_CONSOLE:
                            print(found_string)
            except Exception as ex:
                if PRINT_TO_CONSOLE:
                    print("Error searching for text in website {site}: ".format(site=str(website)) + str(ex))
        driver.quit()
        return found_websites_list

    def close_webdriver(self):
        self.driver.quit()

    def get_website_html_string_with_webdriver(self, driver, website):
        # load website to scrape
        driver.get(website)
        for i in range(1, SCROLL_NUMBER):  # scroll down X times
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.1)
        source = driver.page_source
        return str(source)