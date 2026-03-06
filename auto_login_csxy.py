#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSU campus network auto-login script for 10.0.100.3
Requirements: Python >= 3.8, selenium >= 4, Chrome and chromedriver major versions must match.
"""

import os
import shutil
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

# 1) Account credentials (better move to env vars or local config file)
USERNAME = "LTB20220305117"
PASSWORD = "044557"

# 2) chromedriver path (relative to this script)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROME_DRIVER = os.path.join(BASE_DIR, "tools", "chromedriver", "chromedriver-win64", "chromedriver.exe")
PROFILE_DIR = os.path.join(BASE_DIR, ".chrome-profile")

# 3) Browser options
options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--no-first-run")
options.add_argument("--no-default-browser-check")
options.add_argument("--remote-debugging-port=9222")
options.add_argument(f"--user-data-dir={PROFILE_DIR}")


def is_logged_in_page(driver: webdriver.Chrome) -> bool:
    page = driver.page_source
    page_text = page.lower()
    if "注销" in page or "logout" in page_text:
        return True

    logout_btns = driver.find_elements(By.XPATH, '//input[@name="logout"]')
    return len(logout_btns) > 0


def try_select_campus_network(driver: webdriver.Chrome) -> None:
    """If an ISP option exists, try selecting the campus network option."""
    xpath_candidates = [
        '//input[@value="校园网"]',
        '//input[contains(@value, "校") and contains(@value, "园")]',
        '//input[contains(@onclick, "校园网")]',
    ]

    for xp in xpath_candidates:
        elems = driver.find_elements(By.XPATH, xp)
        for elem in elems:
            try:
                if not elem.is_selected():
                    elem.click()
                print("[INFO] Campus network selected")
                return
            except Exception:
                continue

    print("[INFO] Campus network option not found, skipped")


def main() -> None:
    if not os.path.isfile(CHROME_DRIVER):
        raise FileNotFoundError(f"chromedriver not found: {CHROME_DRIVER}")

    os.makedirs(PROFILE_DIR, exist_ok=True)
    driver = webdriver.Chrome(service=Service(CHROME_DRIVER), options=options)
    driver.set_window_size(900, 700)

    try:
        print("[INFO] Opening login page...")
        driver.get("http://10.0.100.3/")
        time.sleep(2)
        driver.save_screenshot("01_open_page.png")

        if is_logged_in_page(driver):
            print("[SUCC] Already online: detected 注销/Logout page")
            driver.save_screenshot("03_final.png")
            return

        print("[INFO] Filling username/password...")
        wait = WebDriverWait(driver, 10)
        user_box = wait.until(EC.element_to_be_clickable((By.NAME, "DDDDD")))
        pwd_box = wait.until(EC.element_to_be_clickable((By.NAME, "upass")))

        # Use Ctrl+A overwrite in case clear() is ignored on this page
        user_box.send_keys(Keys.CONTROL + "a")
        user_box.send_keys(USERNAME)
        pwd_box.send_keys(Keys.CONTROL + "a")
        pwd_box.send_keys(PASSWORD)

        try_select_campus_network(driver)

        print("[INFO] Submitting form...")
        pwd_box.send_keys("\n")
        time.sleep(5)
        driver.save_screenshot("02_after_submit.png")

        if is_logged_in_page(driver):
            print("[SUCC] Login succeeded: detected 注销/Logout")
        else:
            print("[WARN] Logout not detected; login may have failed. Check 02_after_submit.png")

        driver.save_screenshot("03_final.png")

    finally:
        print("[INFO] Closing browser in 3 seconds...")
        time.sleep(3)
        driver.quit()
        shutil.rmtree(PROFILE_DIR, ignore_errors=True)


if __name__ == "__main__":
    main()
