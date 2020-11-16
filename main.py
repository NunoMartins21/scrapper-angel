from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import os
import json
import traceback
import time
from urllib.parse import urlsplit
import pandas as pd

email = "kewev11524@biiba.com"
passwd = "olaamigo2020"

def save_cookie(driver, path):
    with open(path, 'w') as filehandler:
        json.dump(driver.get_cookies(), filehandler)

def load_cookie(driver, path):
    with open(path, 'r') as cookiesfile:
        cookies = json.load(cookiesfile)
    for cookie in cookies:
        driver.add_cookie(cookie)

def scroll(driver, timeout):
    scroll_pause_time = timeout

    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(scroll_pause_time)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            # If heights are the same it will exit the function
            break
        last_height = new_height

try:
    user_agent = "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.472.63 Safari/534.3"

    """
    options = Options()
    options.add_argument('user-agent=')
    options.add_argument("user-data-dir=./tmp/")
    driver = webdriver.Chrome(options=options)
    """

    profile = webdriver.FirefoxProfile()
    profile.set_preference('dom.webdriver.enabled', False)
    profile.set_preference('useAutomationExtension', False)
    profile.set_preference('general.useragent.override', user_agent)
    profile.update_preferences()
    desired = DesiredCapabilities.FIREFOX

    driver = webdriver.Firefox(firefox_profile=profile, desired_capabilities=desired)

    wait = WebDriverWait(driver, 60)

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

    # Infinite scroll - 12s sleep for each scroll
    # scroll(driver, 12)

    rows = driver.find_elements_by_css_selector("div[data-test=\"StartupResult\"]")

    # From the scrolled page, get all the employers' company links
    for row in rows:
        df = pd.read_excel('scraped.xlsx') if os.path.exists('./scraped.xlsx') else pd.DataFrame(columns=["Company Name", "Company Website"])
        row.find_element_by_css_selector("div:first-child > a:first-child").click() # Open modal
        name = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".ReactModal__Content [class*=\"styles_header\"] > a:nth-child(1) > div:nth-child(2) > div:nth-child(1) > h2:nth-child(1)"))
        ).text
        website = urlsplit(wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".ReactModal__Content [class*=\"styles_website\"] a:first-child"))
        ).get_attribute('href')).netloc.replace('www.', '') # Get website
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".ReactModal__Content button[class*=\"styles_regular\"]:nth-child(2)"))
        ).click()

        df = df.append({
            "Company Name": name,
            "Company Website": website
        }, ignore_index=True)
        df = df.drop_duplicates(subset=["Company Website"], keep="first")
        df.to_excel('scraped.xlsx', index=False)

except KeyboardInterrupt:
    quit()
except Exception as ex:
    traceback.print_exc()