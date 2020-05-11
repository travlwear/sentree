import sys, os
from image_scraper.utils import ImageScraper
from os import listdir
from os.path import isfile, join
from image_scraper.exceptions import PageLoadError, ImageDownloadError, ImageSizeError
import ssim
from PIL import Image

HOME_PATH = os.path.join("..", "..", "..")
GUARDED_IMAGES_FOLDER = os.path.join(HOME_PATH, "sentree", "data", "guarded_images")
DATA_IMAGES_FOLDER = os.path.join(HOME_PATH, "sentree", "data", "images")
MAX_IMAGES = 100
IMAGE_COMPARISON_SSIM_MATCH_THRESHOLD = 0.9
PRINT_TO_CONSOLE = False

class ImageSearch(object):
    def __init__(self, webdriver_path):
        self.webdriver_path = webdriver_path
        self.guarded_images = self.get_guarded_images()

    def get_guarded_images(self):
        return [f for f in listdir(GUARDED_IMAGES_FOLDER) if isfile(join(GUARDED_IMAGES_FOLDER, f))]

    def get_found_images(self):
        self.found_images = [f for f in listdir(DATA_IMAGES_FOLDER) if isfile(join(DATA_IMAGES_FOLDER, f))]
        return self.found_images

    def delete_found_images(self):
        for file in os.scandir(DATA_IMAGES_FOLDER):
            os.remove(file)

    def search_for_guarded_images(self, websites):
        found_websites_list = []
        for website in websites:
            try:
                self.scrape_images(url=website, format_list=["jpg", "png", "jpeg"], download_path=DATA_IMAGES_FOLDER,
                                   use_ghost=True)
                image_found = self.compare_guarded_images_to_found_images()
                if image_found:
                    found_string = "{img} in website: {site}".format(img=image_found, site=str(website))
                    found_websites_list.append(found_string)
                    if PRINT_TO_CONSOLE:
                        print(found_string)

            except PageLoadError as ex:
                if PRINT_TO_CONSOLE:
                    print("Page load error in image search " + str(ex))
            except Exception as ex:
                if PRINT_TO_CONSOLE:
                    print("Error searching for images in website {site}: ".format(site=str(website)) + str(ex))
        self.delete_found_images()

        return found_websites_list

    def compare_guarded_images_to_found_images(self):
        found_images = self.get_found_images()
        for guarded_image in self.guarded_images:
            if "gif" in str(guarded_image):
                for found_image in found_images:
                    if "gif" in str(found_image):
                        if self.compare_gifs(os.path.join(DATA_IMAGES_FOLDER, found_image),
                                                  os.path.join(GUARDED_IMAGES_FOLDER, guarded_image)):
                            return("GIF " + str(guarded_image) + " found")
            else:
                for found_image in found_images:
                    if "gif" not in str(found_image):
                        if self.ssim_compare_images(os.path.join(DATA_IMAGES_FOLDER, found_image),
                                                  os.path.join(GUARDED_IMAGES_FOLDER, guarded_image)):
                            return("Image " + str(guarded_image) + " found")
        return False

    def compare_gifs(self, found_gif, guarded_gif):
        found_gif_size = os.path.getsize(found_gif)
        guarded_gif_size = os.path.getsize(guarded_gif)

        if found_gif_size == guarded_gif_size:
            return True
        else:
            return False

    def ssim_compare_images(self, found_image_file, guarded_image_file):
        # Opens a image in RGB mode
        found_image = Image.open(found_image_file)
        guarded_image = Image.open(guarded_image_file)

        # Size of the image in pixels
        width_found_image, height_found_image = found_image.size
        width_guarded_image, height_guarded_image = guarded_image.size

        cropped = False
        cropped_width = False
        cropped_height = False

        if width_found_image < width_guarded_image and "crop" in str(guarded_image_file):
            width_cropped = width_found_image
            cropped = True
            cropped_width = True
        else:
            width_cropped = width_guarded_image

        if height_found_image < height_guarded_image and "crop" in str(guarded_image_file):
            height_cropped = height_found_image
            cropped = True
            cropped_height = True
        else:
            height_cropped = height_guarded_image

        if cropped:
            # Setting the points for cropped image
            if cropped_width:
                left = int((width_guarded_image-width_cropped)/2)
                right = int(width_guarded_image-((width_guarded_image-width_cropped)/2))
            else:
                left = 0
                right = width_guarded_image
            if cropped_height:
                top = int(height_guarded_image-((height_guarded_image-height_cropped)/2))
                bottom = int((height_guarded_image-height_cropped)/2)
            else:
                bottom = 0
                top = height_guarded_image
            # Cropped image of above dimension
            newsize = (width_cropped, height_cropped)
            top = top - 1
            right = right - 1
            guarded_image_non_cropped = guarded_image.resize(newsize)
            guarded_image = guarded_image.crop((left, bottom, right, top))
            guarded_image = guarded_image.resize(newsize)
        try:
            ssim_value = ssim.compute_ssim(found_image, guarded_image)
            if ssim_value > IMAGE_COMPARISON_SSIM_MATCH_THRESHOLD:
                return True
            else:
                if cropped:
                    ssim_value = ssim.compute_ssim(found_image, guarded_image_non_cropped)
                    if ssim_value > IMAGE_COMPARISON_SSIM_MATCH_THRESHOLD:
                        return True
                return False
        except Exception as ex:
            print("Error comparing images: " + str(ex))
            return False

    def scrape_images(self, url, no_to_download=None,
                      format_list=["jpg", "png", "gif", "svg", "jpeg"],
                      download_path='images', max_filesize=100000000,
                      dump_urls=False, use_ghost=False):

        scraper = ImageScraper()
        scraper.dump_urls = dump_urls
        if use_ghost:
            sys.path.insert(0, self.webdriver_path)
            sys.path.append(self.webdriver_path)
            scraper.use_ghost = use_ghost
        scraper.format_list = format_list
        scraper.url = url
        page_html, page_url = scraper.get_html()
        images = scraper.get_img_list()

        download_path = os.path.join(os.getcwd(), download_path)

        if len(images) == 0:
            return 0, 0  # count, failed
        if no_to_download is None:
            no_to_download = len(images)

        scraper.download_path = download_path
        scraper.process_download_path()

        count = 0
        failed = 0
        over_max_filesize = 0

        for img_url in images:
            if count == no_to_download:
                break
            if count > MAX_IMAGES:
                break
            try:
                scraper.download_image(img_url)
            except ImageDownloadError:
                failed += 1
            except ImageSizeError:
                over_max_filesize += 1
            count += 1
        return count, failed
