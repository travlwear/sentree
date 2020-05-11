import json
import os
HOME_PATH = os.path.join("..", "..", "..")
WEBDRIVER_PATH = os.path.join(HOME_PATH, "sentree", "data", "phantomjs-2.1.1-windows", "bin")
LOG_PATH = os.path.join(HOME_PATH, "sentree", "data", "log")
PUSHBULLET_TOKEN = ''
FILTER_SEARCHES = True
SEND_TO_PUSHBULLET = True
WEBSITE_BATCH_SIZE = 10
GOOGLE_SEARCH_DEPTH = 500

import sys
sys.path.insert(0, HOME_PATH)
import requests
from datetime import datetime
from googlesearch import search
from urllib.error import URLError
from itertools import islice
from sentree.src.crawler.spiders.image_search import ImageSearch
from sentree.src.crawler.spiders.text_search import TextSearch


class GetConfig(object):
    def __init__(self, config_location):
        protected_phrases_file = os.path.join(config_location, "protected_phrases.txt")
        search_keywords_file = os.path.join(config_location, "search_keywords.txt")
        self.searched_websites_file = os.path.join(config_location, "searched_websites.txt")

        self.protected_phrases = self.get_file_contents(protected_phrases_file)
        self.search_keywords = self.get_file_contents(search_keywords_file)
        self.searched_websites = self.get_file_contents(self.searched_websites_file)

    def get_searched_websites(self):
        return self.get_file_contents(self.searched_websites_file)

    def add_searched_websites(self, websites):
        already_searched = self.get_searched_websites()
        combined = already_searched
        for website in websites:
            combined[website] = website

        string = ""
        for website in combined:
            string = string + str(website) + ","

        f = open(self.searched_websites_file, "w")
        f.write(string[:-1])
        f.close()

    def get_file_contents(self, file):
        f = open(file, "r")
        values = {}
        for line in f:
            temp_values = line.split(",")
            for temp_value in temp_values:
                values[temp_value] = temp_value
        f.close()
        return values

class RunSentree(object):
    def __init__(self):
        self.config = GetConfig(os.path.join(HOME_PATH, "sentree", "config"))

    def do_google_searches(self):
        combined_results = {}
        for search_val in self.config.search_keywords:
            try:
                results = search(search_val, tld='com', lang='en', num=10, start=0, stop=GOOGLE_SEARCH_DEPTH, pause=2.0)
                for j in results:
                    temp_val = j
                    combined_results[str(temp_val)] = str(temp_val)
            except URLError as ex:
                print("ERROR in connection. Exception: " + str(ex))

        if FILTER_SEARCHES:
            # get rid of already searched websites
            filtered_combined_results = {}
            for result in combined_results:
                if result not in self.config.searched_websites:
                    filtered_combined_results[result] = result
        else:
            filtered_combined_results = combined_results

        if len(filtered_combined_results) < 1:
            raise Exception("No valid google searches found")
        return filtered_combined_results

    def website_batches(self, data, SIZE=WEBSITE_BATCH_SIZE):
        it = iter(data)
        for i in range(0, len(data), SIZE):
            yield {k: data[k] for k in islice(it, SIZE)}

    def send_found_websites_to_pushbullet(self, found_websites):
        for found_website in found_websites:
            self.send_pushbullet_message(found_website)

    def send_pushbullet_message(self, body):
        msg = {"type": "note", "title": "sentree website warning", "body": body}
        resp = requests.post('https://api.pushbullet.com/v2/pushes',
                             data=json.dumps(msg),
                             headers={'Authorization': 'Bearer ' + PUSHBULLET_TOKEN,
                                      'Content-Type': 'application/json'})
        if resp.status_code != 200:
            print('Error', resp.status_code)

    def create_log(self):
        now = datetime.now()
        dt_string = now.strftime("%d-%m-%Y__%H.%M.%S")
        self.log_name = os.path.join(LOG_PATH, "run_log_for_" + dt_string + ".txt")
        self.log_file = open(self.log_name, "w")
        self.log_file.write("FOUND THE FOLLOWING WEBSITES\n\n")

    def write_sites_to_log(self, log_prepend, found_websites):
        for found_website in found_websites:
            self.log_file.write(log_prepend + " " + str(found_website) + "\n")

    def run_sentree(self):
        found_websites = self.do_google_searches()
        text_search = TextSearch(self.config.protected_phrases, WEBDRIVER_PATH)
        image_search = ImageSearch(WEBDRIVER_PATH)
        self.create_log()

        for websites in self.website_batches(found_websites):
            text_search_found_websites = text_search.search_for_protected_phrases(websites)
            image_search_found_websites = image_search.search_for_guarded_images(websites)
            if SEND_TO_PUSHBULLET:
                self.send_found_websites_to_pushbullet(text_search_found_websites)
                self.send_found_websites_to_pushbullet(image_search_found_websites)
            self.write_sites_to_log("Found website with text search: ", text_search_found_websites)
            self.write_sites_to_log("Found website with image search: ", image_search_found_websites)

            self.config.add_searched_websites(websites)
        self.log_file.close()

if __name__ == "__main__":
    run = RunSentree()
    run.run_sentree()
