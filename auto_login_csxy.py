#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""长沙学院校园网自动登录脚本（首次运行可配置，后续一键登录）。"""

import argparse
import getpass
import json
import os
import shutil
import sys
import time
from typing import Dict, Tuple

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUNTIME_DIR = os.path.join(BASE_DIR, ".runtime")
PROFILE_DIR = os.path.join(RUNTIME_DIR, "chrome-profile")
CONFIG_FILE = os.path.join(BASE_DIR, "campus_login_config.json")

DEFAULT_URL = "http://10.0.100.3/"
USER_FIELD_CANDIDATES = [
    (By.NAME, "DDDDD"),
    (By.ID, "DDDDD"),
    (By.NAME, "username"),
    (By.NAME, "user"),
]
PWD_FIELD_CANDIDATES = [
    (By.NAME, "upass"),
    (By.ID, "upass"),
    (By.NAME, "password"),
    (By.NAME, "passwd"),
]


def detect_chromedriver() -> str:
    candidates = [
        os.path.join(BASE_DIR, "tools", "chromedriver", "chromedriver-win64", "chromedriver.exe"),
        r"C:\Tools\chromedriver\chromedriver-win64\chromedriver.exe",
        r"C:\Windows\System32\chromedriver.exe",
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return ""


def prompt_yes_no(question: str, default_yes: bool = True) -> bool:
    suffix = "[Y/n]" if default_yes else "[y/N]"
    raw = input(f"{question} {suffix}: ").strip().lower()
    if not raw:
        return default_yes
    return raw in {"y", "yes", "1", "true"}


def setup_config(force: bool = False) -> Dict[str, object]:
    if os.path.isfile(CONFIG_FILE) and not force:
        with open(CONFIG_FILE, "r", encoding="utf-8-sig") as f:
            return json.load(f)

    print("[SETUP] 首次配置校园网账号信息")
    username = input("请输入学号/账号: ").strip()
    while not username:
        username = input("账号不能为空，请重新输入: ").strip()

    password = getpass.getpass("请输入密码(输入时不显示): ").strip()
    while not password:
        password = getpass.getpass("密码不能为空，请重新输入: ").strip()

    default_driver = detect_chromedriver()
    if default_driver:
        print(f"[SETUP] 检测到 chromedriver: {default_driver}")
    else:
        print("[SETUP] 未检测到本地 chromedriver，将尝试 Selenium 自动匹配")

    driver_input = input("chromedriver 路径(直接回车=自动): ").strip().strip('"')
    url_input = input(f"登录地址(回车默认 {DEFAULT_URL}): ").strip()
    isp_input = input("运营商关键词(默认: 校园网，可填 联通/移动/电信): ").strip()

    cfg: Dict[str, object] = {
        "username": username,
        "password": password,
        "url": url_input or DEFAULT_URL,
        "chromedriver_path": driver_input or default_driver,
        "isp_keyword": isp_input or "校园网",
        "headless": prompt_yes_no("是否使用无头模式运行", default_yes=True),
        "save_screenshots": prompt_yes_no("是否保存截图用于排错", default_yes=True),
    }

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

    print(f"[SETUP] 配置已保存: {CONFIG_FILE}")
    return cfg


def build_options(headless: bool) -> Options:
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument(f"--user-data-dir={PROFILE_DIR}")
    return options


def create_driver(cfg: Dict[str, object]) -> webdriver.Chrome:
    os.makedirs(RUNTIME_DIR, exist_ok=True)
    shutil.rmtree(PROFILE_DIR, ignore_errors=True)
    os.makedirs(PROFILE_DIR, exist_ok=True)

    options = build_options(bool(cfg.get("headless", True)))
    driver_path = str(cfg.get("chromedriver_path", "")).strip()

    if driver_path:
        if not os.path.isfile(driver_path):
            raise FileNotFoundError(f"chromedriver 不存在: {driver_path}")
        return webdriver.Chrome(service=Service(driver_path), options=options)

    return webdriver.Chrome(options=options)


def has_login_form(driver: webdriver.Chrome) -> bool:
    for by, value in USER_FIELD_CANDIDATES + PWD_FIELD_CANDIDATES:
        elems = driver.find_elements(by, value)
        for elem in elems:
            if elem.is_displayed() and elem.get_attribute("type") != "hidden":
                return True
    return False


def has_logout_button(driver: webdriver.Chrome) -> bool:
    elems = driver.find_elements(
        By.XPATH,
        '//input[translate(@name, "LOGOUT", "logout")="logout" and not(translate(@type, "HIDDEN", "hidden")="hidden")]',
    )
    for elem in elems:
        if elem.is_displayed():
            return True
    return False


def is_logged_in_page(driver: webdriver.Chrome) -> bool:
    if has_login_form(driver):
        return False

    page = driver.page_source
    title = driver.title.strip()
    has_success_hint = ("您已经成功登录" in page) or ("注销页" in title)
    return has_success_hint and has_logout_button(driver)


def try_select_isp(driver: webdriver.Chrome, isp_keyword: str) -> None:
    keyword = (isp_keyword or "").strip()
    if not keyword:
        return

    selects = driver.find_elements(By.NAME, "ISP_select")
    if selects:
        try:
            selector = Select(selects[0])
            for opt in selector.options:
                text = (opt.text or "").strip()
                val = (opt.get_attribute("value") or "").strip()
                if keyword in text or keyword in val:
                    selector.select_by_visible_text(text)
                    print(f"[INFO] 已选择运营商: {text}")
                    return

            if keyword == "校园网":
                for opt in selector.options:
                    val = (opt.get_attribute("value") or "").lower()
                    if "xyw" in val:
                        selector.select_by_value(opt.get_attribute("value"))
                        print("[INFO] 已选择运营商: 校园网(@xyw)")
                        return

            print(f"[INFO] 未匹配到运营商关键字: {keyword}，保持页面默认值")
            return
        except Exception:
            pass

    xpath_candidates = [
        '//input[@value="校园网"]',
        '//input[contains(@value, "校") and contains(@value, "园")]',
        '//input[contains(@onclick, "校园网")]',
    ]
    for xp in xpath_candidates:
        for elem in driver.find_elements(By.XPATH, xp):
            try:
                if not elem.is_selected():
                    elem.click()
                print("[INFO] 已选择运营商：校园网")
                return
            except Exception:
                continue

    print("[INFO] 未找到可切换运营商控件，跳过")


def find_login_boxes(driver: webdriver.Chrome, timeout: int = 10) -> Tuple[object, object]:
    deadline = time.time() + timeout
    while time.time() < deadline:
        user_box = None
        pwd_box = None

        for by, value in USER_FIELD_CANDIDATES:
            elems = driver.find_elements(by, value)
            for elem in elems:
                if elem.is_displayed() and elem.get_attribute("type") != "hidden":
                    user_box = elem
                    break
            if user_box:
                break

        for by, value in PWD_FIELD_CANDIDATES:
            elems = driver.find_elements(by, value)
            for elem in elems:
                if elem.is_displayed() and elem.get_attribute("type") != "hidden":
                    pwd_box = elem
                    break
            if pwd_box:
                break

        if user_box and pwd_box:
            return user_box, pwd_box

        time.sleep(0.5)

    raise TimeoutException("未找到账号/密码输入框")


def maybe_save_screenshot(driver: webdriver.Chrome, enabled: bool, filename: str) -> None:
    if enabled:
        driver.save_screenshot(os.path.join(BASE_DIR, filename))


def run_login(cfg: Dict[str, object]) -> int:
    driver = create_driver(cfg)
    driver.set_window_size(1280, 800)
    save_screenshots = bool(cfg.get("save_screenshots", True))

    try:
        url = str(cfg.get("url", DEFAULT_URL)).strip() or DEFAULT_URL
        print(f"[INFO] 打开页面: {url}")
        driver.get(url)
        time.sleep(2)
        maybe_save_screenshot(driver, save_screenshots, "01_open_page.png")

        if is_logged_in_page(driver):
            print("[SUCC] 当前已在线（检测到注销页）")
            maybe_save_screenshot(driver, save_screenshots, "03_final.png")
            return 0

        print("[INFO] 填写账号密码...")
        try:
            user_box, pwd_box = find_login_boxes(driver, timeout=12)
        except TimeoutException:
            with open(os.path.join(BASE_DIR, "debug_unknown_state.html"), "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("[WARN] 页面状态异常：未识别到登录框，也未识别到有效注销页")
            maybe_save_screenshot(driver, save_screenshots, "03_final.png")
            return 3

        user_box.send_keys(Keys.CONTROL + "a")
        user_box.send_keys(str(cfg["username"]))
        pwd_box.send_keys(Keys.CONTROL + "a")
        pwd_box.send_keys(str(cfg["password"]))

        try_select_isp(driver, str(cfg.get("isp_keyword", "校园网")))

        print("[INFO] 提交登录...")
        pwd_box.send_keys("\n")
        time.sleep(5)
        maybe_save_screenshot(driver, save_screenshots, "02_after_submit.png")

        if is_logged_in_page(driver):
            print("[SUCC] 登录成功：检测到注销页")
            maybe_save_screenshot(driver, save_screenshots, "03_final.png")
            return 0

        print("[WARN] 未检测到有效注销页，可能登录失败")
        with open(os.path.join(BASE_DIR, "debug_unknown_state.html"), "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        maybe_save_screenshot(driver, save_screenshots, "03_final.png")
        return 2

    finally:
        print("[INFO] 关闭浏览器")
        driver.quit()
        shutil.rmtree(PROFILE_DIR, ignore_errors=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="长沙学院校园网自动登录")
    parser.add_argument("--init", action="store_true", help="重新进入首次配置向导")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        cfg = setup_config(force=args.init)
    except Exception as e:
        print(f"[ERR] 配置读取/写入失败: {e}")
        return 1

    required = ["username", "password"]
    missing = [k for k in required if not str(cfg.get(k, "")).strip()]
    if missing:
        print(f"[ERR] 配置缺失字段: {', '.join(missing)}")
        print("[INFO] 请运行: python auto_login_csxy.py --init")
        return 1

    try:
        return run_login(cfg)
    except Exception as e:
        print(f"[ERR] 运行失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
