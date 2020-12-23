from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import TimeoutException
import os
import json
import traceback
import time
from urllib.parse import urlsplit
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

email = os.getenv('email')
passwd = os.getenv('password')

def save_cookie(driver, path):
    with open(path, 'w') as filehandler:
        json.dump(driver.get_cookies(), filehandler)

def load_cookie(driver, path):
    with open(path, 'r') as cookiesfile:
        cookies = json.load(cookiesfile)
    for cookie in cookies:
        driver.add_cookie(cookie)

def process_info(driver):
    print("Start processing info...")
    rows = driver.find_elements_by_css_selector("div[data-test=\"StartupResult\"]")

    # Go up again to avoid problems
    driver.execute_script("window.scrollTo(0, 0);")

    # From the scrolled page, get all the employers' company links
    for row in rows:
        df = pd.read_excel('scraped.xlsx') if os.path.exists('./scraped.xlsx') else pd.DataFrame(columns=["Company Name", "Company Website"])
        row.find_element_by_css_selector("div:first-child > a:first-child").click() # Open modal
        name = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".ReactModal__Content [class*=\"styles_header\"] h2"))
        ).text
        website_el = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".ReactModal__Content [class*=\"styles_website\"] a:first-child"))
        ).get_attribute('href')
        website = urlsplit(website_el).netloc.replace('www.', '') if website_el else "-" # Get website
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".ReactModal__Content button[class*=\"styles_regular\"]:nth-child(2)"))
        ).click()

        df = df.append({
            "Company Name": name,
            "Company Website": website
        }, ignore_index=True)
        df = df.drop_duplicates(subset=["Company Website"], keep="last")
        df.to_excel('scraped.xlsx', index=False)

        time.sleep(1)

    # Go up again to avoid problems
    driver.execute_script("window.scrollTo(0, 0);")
    print("Done processing info")

try:
    user_agent = "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.472.63 Safari/534.3"

    profile = webdriver.FirefoxProfile()
    profile.set_preference('dom.webdriver.enabled', False)
    profile.set_preference('useAutomationExtension', False)
    profile.set_preference('general.useragent.override', user_agent)
    profile.update_preferences()
    desired = DesiredCapabilities.FIREFOX

    driver = webdriver.Firefox(firefox_profile=profile, desired_capabilities=desired)

    wait = WebDriverWait(driver, 600)

    # Login
    driver.get('https://angel.co/login')
    wait.until(
        EC.presence_of_element_located((By.ID, "user_email"))
    )
    email_el = driver.find_element_by_id('user_email')
    email_el.send_keys(email)
    passwd_el = driver.find_element_by_id('user_password')
    passwd_el.send_keys(passwd)
    btn = driver.find_element_by_css_selector('#new_user > div:nth-child(6) > input')
    btn.click()
    save_cookie(driver, './cookie.json')
    
    table_url = "https://angel.co/jobs"
    driver.get(table_url)

    # Scrolling
    load = 9 # divs loaded at each scrolling - number of divs removed
    scroll_pause_time = 8

    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(scroll_pause_time)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")

        try:
            if new_height == last_height:
                # If heights are the same it will exit the function
                print("Heights are the same, so it's the end")
                process_info(driver)
                break
            else:
                last_height = new_height

                process_info(driver)

                row_nr = int(driver.execute_script("return document.querySelectorAll(\"div[data-test*='JobSearchResults'] div[data-test*='StartupResult']\").length;")) - 2

                # Delete first all rows, except for two
                for i in range(0, row_nr):
                    driver.execute_script(f"document.querySelector(\"div[data-test*='JobSearchResults'] div[data-test*='StartupResult']\").remove()")

                time.sleep(5)
        except TimeoutException as ex:
            print("Timeout exception")
            wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".ReactModal__Content button[class*=\"styles_regular\"]:nth-child(2)"))
            ).click()
            continue
except KeyboardInterrupt:
    quit()
except Exception as ex:
    traceback.print_exc()