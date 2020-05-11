# sentree

## Dependencies:
 - Python 3
 - pip -r install the included requirements.txt

## How to configure
 - Drop images that you would like to match against for in data\guarded_images
 - Add phrases that you would like to match against in config\protected_phrases.txt
 - Add the google searches you would like to use in config\search_keywords
 - Configure the code run contants. e.g. the hardcoded config values. Key values to look at are in runner.py, image_search.py, and text_search.py and are:
 	- FILTER_SEARCHES: can choose whether to include dict of previous searches as valid websites to search or not.
 	- SEND_TO_PUSHBULLET: Will send notifications to phone app if set to True.
 	- WEBSITE_BATCH_SIZE: Used a loop value when parsing though returned google search.
 	- GOOGLE_SEARCH_DEPTH: Determines how many the max websites the google searches will return.
 	- IMAGE_COMPARISON_SSIM_MATCH_THRESHOLD: Value between 0-1 that determines how the close the match between 2 images has to be.
 	- PRINT_TO_CONSOLE: When set to true will print matches to consol

## How to run
- Navigate to src/crawler
- Execute *python runner.py*
- All results will be found in the timestamped log in data/log after the run has completed

## PushBullet (Optional)
Can use PushBullet to send matches in real time to a phone. In order to do so set up PushBullet on a phone and set the config value PUSHBULLET_TOKEN to the correct value.


 ### TODO
 - Change hardcoded config values to properties file
 - Change google search for images to google image search
 - Update to headless selenium webdriver
 - Improve image recognition