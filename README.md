# LLM AI Gateway Dashboard

SWE30009 Software Testing and Reliability, Project (Semester 2, 2026)

Hassan Ali Shah SYED (105797705)

[![Test Ubuntu](../../actions/workflows/test-ubuntu.yml/badge.svg)](../../actions/workflows/test-ubuntu.yml)
[![Test Windows](../../actions/workflows/test-windows.yml/badge.svg)](../../actions/workflows/test-windows.yml)

## About

A small web application for an LLM AI gateway. The user enters the usage of each
model in million tokens and presses **Calculate Usage**. The page then shows a
summary of the models used and the total amount to pay.

- 8 models from 5 providers, each with a price per 1 million tokens
- Batch API switch that takes 50% off the price of every model
- 6% Sales and Service Tax (SST) added to the bill
- Invalid input (letters, negative numbers, more than 2 decimal places, usage
  above 10,000 million tokens) is rejected with a message and no bill is shown

The application is tested automatically with Selenium. The test cases are read
from a CSV file.

## Files

| File | Purpose |
|---|---|
| `index.html` | The web application (HTML, CSS and JavaScript in one file) |
| `test_cases.csv` | 10 test cases with their expected results |
| `test_gateway.py` | Selenium test script, run with pytest |
| `requirements.txt` | Python packages needed to run the tests |
| `.github/workflows/test-ubuntu.yml` | GitHub Actions workflow that runs the tests on Ubuntu |
| `.github/workflows/test-windows.yml` | GitHub Actions workflow that runs the tests on Windows |

## Run the application

1. Put this folder in `C:\xampp\htdocs\` as `ai-gateway-project`.
2. Start Apache in XAMPP.
3. Open <http://localhost/ai-gateway-project/index.html>.

## Run the tests

```
python -m pip install -r requirements.txt
python -m pytest test_gateway.py -s -v
```

Each row of `test_cases.csv` runs as its own test. For every test case the
script prints the inputs, the expected and actual values, and `[PASS]` or
`[FAIL]`. A screenshot of the page is saved in the `screenshots` folder, named
after the test case and its result, for example `TC01_PASS.png`.

If the application is at a different address, set `APP_URL` first:

```
# PowerShell
$env:APP_URL = "http://localhost/other-folder/index.html"

# Command Prompt
set APP_URL=http://localhost/other-folder/index.html
```

Other optional settings, set the same way:

| Setting | Effect |
|---|---|
| `HEADLESS=1` | Run Chrome without a window |
| `CHROME_BINARY` | Path to a specific Chrome executable |
| `CHROMEDRIVER_PATH` | Path to a specific chromedriver executable |

## Test cases

| ID | What it checks |
|---|---|
| TC01 | Single model at standard price |
| TC02 | All eight models at standard price |
| TC03 | All eight models with batch discount |
| TC04 | Decimal usage and an explicit zero |
| TC05 | Half-sen rounding with batch discount |
| TC06 | Upper boundary of 10,000 million tokens |
| TC07 | Just above the upper boundary (rejected) |
| TC08 | All usage fields left blank (rejected) |
| TC09 | Negative usage beside a valid value (rejected) |
| TC10 | Non-numeric usage beside a valid value (rejected) |

## Continuous integration

The tests also run on GitHub Actions, so they do not depend on my own PC.
The badges at the top of this page show whether the latest run of each
workflow passed.

| Workflow | Runner | Trigger | Time limit | Screenshots artifact |
|---|---|---|---|---|
| `test-ubuntu.yml` | `ubuntu-latest` | Manual (`workflow_dispatch`) | 30 minutes | `screenshots-ubuntu` |
| `test-windows.yml` | `windows-latest` | Manual (`workflow_dispatch`) | 30 minutes | `screenshots-windows` |

To run one: open the **Actions** tab, choose **Test Ubuntu** or
**Test Windows**, then press **Run workflow**.

Both workflows do the same key steps: check out the repository, set up
Python, install the packages in `requirements.txt`, check that Chrome and
ChromeDriver are available, start a web server for `index.html`, and run
`test_gateway.py`. The same test script and test cases are used on both
systems. Only the setup steps differ:

| Step | Ubuntu | Windows |
|---|---|---|
| Shell | Bash | PowerShell |
| Find Chrome and ChromeDriver | Commands on the `PATH` | `.exe` files in fixed folders, passed to the tests as full paths |
| Read the Chrome version | `google-chrome --version` | Read from the file properties of `chrome.exe` |
| Start the web server in the background | `nohup ... &` | `Start-Process` |
| Web server and tests | Separate steps; the server keeps running between steps | One step; a server started in its own step was no longer running in the next step |
| Wait for the web server | `curl` in a loop | `Invoke-WebRequest` in a loop |
| Text encoding of the test output | UTF-8 by default | Set to UTF-8 with `PYTHONUTF8` |
