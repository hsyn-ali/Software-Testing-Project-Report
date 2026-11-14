"""
SWE30009 Project - automated functional test for the LLM AI Gateway Dashboard.

Reads the test cases from test_cases.csv, feeds each one into the web
application with Selenium, compares the actual result with the expected
result and prints PASS / FAIL for every test case.

Each row of the CSV file runs as its own test, so 10 rows give 10 tests.

Run:  python -m pytest test_gateway.py -s -v
Optional environment variables:
  APP_URL            page to test (default http://localhost/ai-gateway-project/index.html)
  HEADLESS           set to 1 to run the browser without a window
  CHROME_BINARY      path to a specific Chrome executable
  CHROMEDRIVER_PATH  path to a specific chromedriver executable
"""

import csv
import os
import re
import shutil
import sys
import time
from decimal import Decimal, InvalidOperation

import pytest
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Never let an unusual character crash the console output (matters on Windows).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")

APP_URL = os.environ.get("APP_URL", "http://localhost/ai-gateway-project/index.html")
HEADLESS = os.environ.get("HEADLESS", "0") == "1"
FOLDER = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(FOLDER, "test_cases.csv")
SCREENSHOT_FOLDER = os.path.join(FOLDER, "screenshots")
WAIT_SECONDS = 5

MODEL_IDS = ["gpt-4o", "gpt-4o-mini", "claude-sonnet-4", "claude-haiku-3-5",
             "gemini-2-5-pro", "gemini-2-5-flash", "llama-3-3-70b", "mistral-large"]
AMOUNT_FIELDS = ["subtotal", "discount", "sst", "total"]
REQUIRED_COLUMNS = (["test_id", "description"] + MODEL_IDS + ["batch", "expected_models_used"]
                    + ["expected_" + field for field in AMOUNT_FIELDS] + ["expected_error"])

RESULTS = []  # (test_id, description, status, seconds) for the summary at the end

# ---------- (a) Read the test cases from the CSV file ----------
# This runs before any browser is opened, so a mistake in the test data is
# reported clearly instead of stopping the run halfway.
if not os.path.exists(CSV_FILE):
    raise FileNotFoundError("cannot find the CSV file: " + CSV_FILE)

with open(CSV_FILE, newline="", encoding="utf-8-sig") as file:
    reader = csv.DictReader(file)
    columns = reader.fieldnames or []
    TEST_CASES = list(reader)

missing = [column for column in REQUIRED_COLUMNS if column not in columns]
if missing:
    raise ValueError("the CSV file is missing these columns: " + ", ".join(missing))
if not TEST_CASES:
    raise ValueError("the CSV file has no test cases")

TEST_IDS = [(case["test_id"] or "").strip() for case in TEST_CASES]
for row_number, case in enumerate(TEST_CASES, start=2):
    if (case["test_id"] or "").strip() == "":
        raise ValueError("CSV row {}: test_id is empty".format(row_number))
    if (case["batch"] or "").strip().lower() not in ("yes", "no"):
        raise ValueError("CSV row {}: batch must be yes or no".format(row_number))
if len(set(TEST_IDS)) != len(TEST_IDS):
    raise ValueError("the CSV file has repeated test_id values")


@pytest.fixture(scope="module")
def driver():
    """Runs once: launch Chrome before the first test case, close it after the last."""

    # Start every run with an empty screenshots folder so old results cannot mislead.
    if os.path.exists(SCREENSHOT_FOLDER):
        shutil.rmtree(SCREENSHOT_FOLDER)
    os.makedirs(SCREENSHOT_FOLDER, exist_ok=True)

    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-first-run")
    if HEADLESS:
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1440,1000")

    # Which Chrome and chromedriver to use:
    #   1. the paths in CHROME_BINARY / CHROMEDRIVER_PATH, if they are set
    #   2. the Tutorial 7 folders next to this script, if they are there
    #   3. otherwise the Chrome installed on this computer
    chrome_path = os.environ.get("CHROME_BINARY", "")
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH", "")
    tutorial_chrome = os.path.join(FOLDER, "chrome-win32", "chrome.exe")
    tutorial_chromedriver = os.path.join(FOLDER, "chromedriver-win32", "chromedriver.exe")
    if chrome_path == "" and chromedriver_path == "" and os.path.exists(tutorial_chrome) and os.path.exists(tutorial_chromedriver):
        chrome_path = tutorial_chrome
        chromedriver_path = tutorial_chromedriver
    if chrome_path != "":
        options.binary_location = chrome_path

    # ---------- (b) Launch a web browser instance ----------
    try:
        if chromedriver_path != "":
            browser = webdriver.Chrome(service=Service(chromedriver_path), options=options)
        else:
            browser = webdriver.Chrome(options=options)
    except WebDriverException as error:
        pytest.exit("could not start Chrome: " + (error.msg or "unknown").splitlines()[0], returncode=2)

    if not HEADLESS:
        browser.maximize_window()

    print()
    print("Testing", APP_URL)
    print("Loaded", len(TEST_CASES), "test cases from", os.path.basename(CSV_FILE))
    start_all = time.time()

    yield browser

    browser.quit()

    # ---------- Summary of the whole run ----------
    passed = sum(1 for result in RESULTS if result[2] == "PASS")
    print()
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    for test_id, description, status, seconds in RESULTS:
        print("{:<6} {:<5} {:>6.2f} s  {}".format(test_id, status, seconds, description))
    print("-" * 70)
    print("Total: {}   Passed: {}   Failed: {}   Time: {:.2f} s".format(len(RESULTS), passed, len(RESULTS) - passed, time.time() - start_all))
    print("Screenshots saved in", SCREENSHOT_FOLDER)


# ---------- (g) Repeat (c) to (f) for every test case: one test per CSV row ----------
@pytest.mark.parametrize("case", TEST_CASES, ids=TEST_IDS)
def test_gateway(driver, case):
    wait = WebDriverWait(driver, WAIT_SECONDS)
    test_id = case["test_id"].strip()
    start = time.time()
    reason = ""  # stays empty when the test case passes
    print()
    print("=" * 70)
    print(test_id, "-", case["description"])
    print("=" * 70)

    try:
        # ---------- (c) Navigate to the web application ----------
        driver.get(APP_URL)
        wait.until(EC.element_to_be_clickable((By.ID, "calculate-btn")))

        # ---------- (d) Feed the test case in and click Calculate Usage ----------
        for model_id in MODEL_IDS:
            value = (case[model_id] or "").strip()
            if value != "":
                box = driver.find_element(By.ID, "usage-" + model_id)
                box.clear()
                box.send_keys(value)
                print("  input     {:<18} {}".format(model_id, value))

        batch = case["batch"].strip().lower()
        toggle = driver.find_element(By.ID, "batch-toggle")
        if toggle.is_selected() != (batch == "yes"):
            toggle.click()
        print("  input     {:<18} {}".format("batch", batch))

        driver.find_element(By.ID, "calculate-btn").click()

        # ---------- (e) Compare the actual result with the expected result ----------
        expected_error = (case["expected_error"] or "").strip()
        bill = driver.find_element(By.ID, "bill")
        banner = driver.find_element(By.ID, "error-message")
        problems = []

        if expected_error != "":
            # Invalid input: an error message must appear and no bill may be shown.
            try:
                wait.until(EC.visibility_of(banner))
                print("  error     expected to contain '{}'".format(expected_error))
                print("            actual '{}'".format(banner.text.strip()))
                if expected_error.lower() not in banner.text.lower():
                    problems.append("error message does not contain '" + expected_error + "'")
            except TimeoutException:
                problems.append("no error message was shown")
            if bill.is_displayed():
                problems.append("a bill was shown for invalid input")
        else:
            # Valid input: the bill must appear with the expected amounts.
            try:
                wait.until(EC.visibility_of(bill))
            except TimeoutException:
                problems.append("no bill was shown" + (" (error: " + banner.text.strip() + ")" if banner.is_displayed() else ""))

            if bill.is_displayed():
                for field in AMOUNT_FIELDS:
                    actual_text = driver.find_element(By.ID, field).text
                    actual = Decimal(re.sub(r"[^0-9.]", "", actual_text))
                    expected = Decimal(case["expected_" + field].strip())
                    match = actual == expected
                    print("  {:<10}expected {:>12}   actual {:>12}   {}".format(field, expected, actual, "ok" if match else "MISMATCH"))
                    if not match:
                        problems.append("{} expected {} but got {}".format(field, expected, actual))

                actual_models = len(driver.find_elements(By.CSS_SELECTOR, "#summary-rows tr"))
                expected_models = int(case["expected_models_used"].strip())
                match = actual_models == expected_models
                print("  {:<10}expected {:>12}   actual {:>12}   {}".format("models", expected_models, actual_models, "ok" if match else "MISMATCH"))
                if not match:
                    problems.append("models used expected {} but got {}".format(expected_models, actual_models))

                if banner.is_displayed():
                    problems.append("an error message was shown for valid input")

        reason = "; ".join(problems)

    except TimeoutException:
        reason = "the page did not load within {} seconds. Is the web server running at {}?".format(WAIT_SECONDS, APP_URL)
    except WebDriverException as error:
        reason = "browser error: " + (error.msg or "unknown").splitlines()[0]
        if "ERR_CONNECTION" in reason:
            reason = reason + ". Is the web server running at " + APP_URL + "?"
    except (InvalidOperation, ValueError, AttributeError) as error:
        reason = "bad value in test case or page: {}".format(error)

    status = "PASS" if reason == "" else "FAIL"

    # Screenshot of the web application, named after the test case and its status.
    # Scroll the total (or the error message) into view first so it is never cut off.
    screenshot = os.path.join(SCREENSHOT_FOLDER, "{}_{}.png".format(test_id, status))
    try:
        visible = [element for element in driver.find_elements(By.CSS_SELECTOR, "#total, #error-message") if element.is_displayed()]
        if visible:
            driver.execute_script("arguments[0].scrollIntoView({block: 'end'});", visible[0])
        driver.save_screenshot(screenshot)
    except WebDriverException:
        screenshot = "(screenshot could not be saved)"

    # ---------- (f) Display the pass/fail status ----------
    seconds = time.time() - start
    if reason != "":
        print("  reason:", reason)
    print("  Screenshot:", os.path.basename(screenshot))
    print("  [{}] {} {}  ({:.2f} s)".format(status, test_id, "passed" if status == "PASS" else "failed", seconds))
    RESULTS.append((test_id, case["description"], status, seconds))

    # Using pytest: a failed assert marks this test case as failed and sets the exit code
    assert reason == "", reason
