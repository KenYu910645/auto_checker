#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
# from selenium.webdriver.support.ui import Select
import cv2
from PIL import Image
import numpy as np
import pytesseract
import io
import re
import pprint
import logging 
from collections import namedtuple, defaultdict
import datetime
import time 
import requests
import random 


#--- parameters ----# 
# Encoder webside: https://www.ewdna.com/2008/12/online-urlencoderutf-8.html
BirthDate = namedtuple("BirthDate", ["year", "month", "day"])

# 廖庭蔚
# ENTRY_WEBSIDE = "https://reg.ntuh.gov.tw/webadministration/DoctorServiceQueryByDrName.aspx?HospCode=T0&QueryName=%E5%BB%96%E5%BA%AD%E8%94%9A"
# 侯君翰
# ENTRY_WEBSIDE = "https://reg.ntuh.gov.tw/webadministration/DoctorServiceQueryByDrName.aspx?HospCode=T0&QueryName=%e4%be%af%e5%90%9b%e7%bf%b0"
# 宋子茜
ENTRY_WEBSIDE = "https://reg.ntuh.gov.tw/webadministration/DoctorServiceQueryByDrName.aspx?HospCode=T0&QueryName=%E5%AE%8B%E5%AD%90%E8%8C%9C"
IS_GUI = False
PATH_TO_DRIVER = "/home/lab530/KenYu/auto_checker/chromedriver"

# Ken's info
ID_NUM = "HXXXXXXXXX"
BIRTH = BirthDate(year="12", month="34", day="56")
#
WAIT_TIME = 5 # sec

##################
####  logger   ###
##################
# Set up logger
formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger('auto_checker')
logger.setLevel(logging.DEBUG)

# Print out logging message on console
h_console = logging.StreamHandler()
h_console.setFormatter(formatter)
h_console.setLevel(logging.INFO)
logger.addHandler(h_console)

# Record logging message at logging file
h_file = logging.FileHandler("auto_checker.log")
h_file.setFormatter(formatter)
h_file.setLevel(logging.INFO)
logger.addHandler(h_file)

class Spider():
    def __init__(self):
        #---- Get uri content -------# 
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('--disable-extensions')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--no-sandbox') # Run chrome with root
        self.options.add_argument('--headless') # Run chrome without GUI
        self.options.add_argument('--ignore-certificate-errors')

    def val_img_parser(self, img):
        
        hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # HSV color thresholding
        mask = cv2.inRange(hsv_img, (0, 255, 0), (255, 255, 255))

        # Create a structuring element for erosion
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))  # Adjust the kernel size as needed

        # Erode + dilate pixels
        mask = cv2.erode (mask, kernel, iterations=1)
        mask = cv2.dilate(mask, kernel, iterations=1)

        # Reverse white and black
        mask = cv2.bitwise_not(mask)

        # Parse the mask with tesseract
        result_txt = pytesseract.image_to_string(mask, lang="eng")
        logger.info(f"Parse Result (Before Filter): {repr(result_txt)}")

        # Filter all special characters
        result_txt = re.sub(r"[^a-zA-Z0-9]", "", result_txt)
        logger.info(f"Parse Result (After Filter): {repr(result_txt)}")
        
        return result_txt

    def auto_check(self):
        logger.info("Start auto checking routine.")
        browser = webdriver.Chrome(service = Service(PATH_TO_DRIVER), options=self.options)
        logger.info("Finish browser")
        
        # Access entry website
        browser.get(ENTRY_WEBSIDE)

        # Wait until the input txt is avilable, meaning the page is loaded 
        wait = WebDriverWait(browser, WAIT_TIME)
        element_grid = wait.until(EC.presence_of_element_located((By.ID, "DoctorServiceListInSeveralDaysInput_GridViewDoctorServiceList")))
        print(element_grid.text)
        
        
        # Find all hyperlink elements on the page
        element_link = element_grid.find_elements(By.TAG_NAME, "a")
        
        if len(element_link)== 0:
            logger.info("The doctor is full, no appointment available.")
        
        # TODO maybe i want to check 限本科複診 * before doing link
        
        # Loop through the hyperlink elements
        # print(link)
        # for link in element_link:
        # Get the text or other attributes of the hyperlink element
        # print(link.text)
        
        app_link = None
        for link in element_link:
            if link.text == "掛號":
                app_link = link
        
        if app_link == None:
            logger.info("Nno appointment available.")
            return 
        
        # Click on the hyperlink
        app_link.click()
        
        # Wait the page to load, until the input txt is avilable
        element_input_id = WebDriverWait(browser, WAIT_TIME).until(EC.presence_of_element_located((By.ID, "txtIuputID")))
        element_input_id.send_keys(ID_NUM)
        logger.info("Typed in ID number")
        
        # Select ID number click box
        element_option_box = browser.find_element(By.ID, "radInputNum_0")
        element_option_box.click()
        logger.info("Click checkbox")
        
        # Input birth year
        time.sleep(0.1)
        element_birth_year = WebDriverWait(browser, WAIT_TIME).until(EC.presence_of_element_located((By.ID, "ddlBirthYear")))
        logger.info(f"Selected birth year: {BIRTH.year}")
        select = Select(element_birth_year)
        select.select_by_visible_text(BIRTH.year)

        # Input birth month
        time.sleep(0.1)
        element_birth_month = WebDriverWait(browser, WAIT_TIME).until(EC.presence_of_element_located((By.ID, "ddlBirthMonth")))
        select = Select(element_birth_month)
        select.select_by_visible_text(BIRTH.month)
        logger.info(f"Selected Birth month: {BIRTH.month}")
        
        # Input birth day
        time.sleep(0.1)
        element_birth_day = WebDriverWait(browser, WAIT_TIME).until(EC.presence_of_element_located((By.ID, "ddlBirthDay")))
        select = Select(element_birth_day)
        select.select_by_visible_text(BIRTH.day)
        logger.info(f"Selected birth day {BIRTH.day}")

        # Get the image source URL
        element_img = browser.find_element(By.ID, "imgVlid")
        image_src = element_img.get_attribute("src")
        response = requests.get(image_src)
        if response.status_code == 200:
            # Convert the response content to a NumPy array
            img = np.array( Image.open(io.BytesIO(response.content)).convert("RGB") )

            # Parse the validation image
            val_img_str = self.val_img_parser(img)
            
            # Type in validation txt
            element_val_str = WebDriverWait(browser, WAIT_TIME).until(EC.presence_of_element_located((By.ID, "txtVerifyCode")))
            element_val_str.clear()
            element_val_str.send_keys(val_img_str)

        else:
            logger.error(f"Fail to download validation image.")
        
        # # Click the confirmation button
        # element_confirm_button = WebDriverWait(browser, WAIT_TIME).until(EC.presence_of_element_located((By.ID, "btnOK")))
        # element_confirm_button.click()
        # logger.info(f"Clicked the confirm button")
        
        # Click the cleaning button, this is for testing
        element_clean_button = WebDriverWait(browser, WAIT_TIME).until(EC.presence_of_element_located((By.ID, "btnClear")))
        element_clean_button.click()
        logger.info(f"Clicked the clean button")
        
     
def main ():
    spider = Spider()
    spider.auto_check()

if __name__ == '__main__':
    print ("Start autochecker")
    main()
    print ("End autochecker")


