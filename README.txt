LLM AI Gateway Dashboard - SWE30009 Project

Files
  index.html        the web application (HTML, CSS and JavaScript in one file)
  test_cases.csv    10 test cases with expected results
  test_gateway.py   Selenium test script (pytest, as in the Week 10 tutorial)
  requirements.txt  Python packages needed

Setup
  1. Put this whole folder in C:\xampp\htdocs\ so it is
     C:\xampp\htdocs\ai-gateway-project\ and start Apache in XAMPP.
     Open http://localhost/ai-gateway-project/index.html to check it works.
  2. python -m pip install -r requirements.txt
  3. Optional: copy the chrome-win32 and chromedriver-win32 folders from
     tutorial7_working_dir into this folder (next to test_gateway.py).
     If they are missing, the script uses the Chrome installed on your PC.

Run the tests (from inside this folder)
  python -m pytest test_gateway.py -s -v
  Each row of test_cases.csv runs as its own test, so the result shows 10 tests.
  Screenshots are saved in the screenshots folder as TC01_PASS.png, TC01_FAIL.png, ...
  Do not close the Chrome window while the tests are running.

Optional settings (set before running)
  PowerShell:      $env:APP_URL = "http://localhost/other-folder/index.html"
  Command Prompt:  set APP_URL=http://localhost/other-folder/index.html
  Other settings, set the same way:
    HEADLESS=1                 run Chrome without a window
    CHROME_BINARY=...          path to a specific chrome.exe
    CHROMEDRIVER_PATH=...      path to a specific chromedriver.exe

Editing test_cases.csv
  Use Notepad or VS Code, not Excel. Excel changes values such as 0.50 to 0.5.
