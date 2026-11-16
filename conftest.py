"""
conftest.py - automated test report (Extension Task 3).

pytest loads this file by itself. Together with the pytest-html plugin it
turns a normal test run into an HTML report:

    python -m pytest test_gateway.py -s -v --html=report/test-report.html --self-contained-html

What this file adds to the standard pytest-html report:
  * a results overview at the top of the report: total, passed and failed
    test cases, the pass rate, a pass/fail bar, a chart of the execution time
    of every test case, and a list of the failed test cases with the reason
  * the screenshot of every test case, inside its row of the results table
  * a Description column in the results table
  * on GitHub Actions: a results table on the Summary page of the run
"""

import base64
import html
import os
import platform
import time
from datetime import datetime

import pytest

try:
    from pytest_html import extras as report_extras
except ImportError:  # the tests still run without the report plugin
    report_extras = None

# The pytest_html_... functions below are marked "optionalhook" so that the
# tests also run on a computer where pytest-html is not installed.

CASE_RESULTS = []   # one dictionary per test case, filled in while the tests run
RUN_INFO = {"start": time.time(), "chrome": "unknown"}


def pytest_sessionstart(session):
    """Remember when the run started, to report the total execution time."""
    RUN_INFO["start"] = time.time()


@pytest.hookimpl(optionalhook=True)
def pytest_html_report_title(report):
    """Title shown at the top of the HTML report."""
    report.title = "LLM AI Gateway Dashboard - Selenium Test Report"


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Runs after every test case: record its result and attach its screenshot."""
    outcome = yield
    report = outcome.get_result()

    # Each test case is reported in three phases (setup, call, teardown).
    # "call" is the test itself. A failed "setup" means the browser could not start.
    if report.when != "call" and not (report.when == "setup" and report.failed):
        return

    test_id = item.callspec.id if hasattr(item, "callspec") else item.name
    case = item.callspec.params.get("case", {}) if hasattr(item, "callspec") else {}
    description = case.get("description", "") if isinstance(case, dict) else ""
    passed = report.passed

    # Short reason for a failure: the first line of the assertion message.
    reason = ""
    if not passed and call.excinfo is not None:
        reason = str(call.excinfo.value).strip().splitlines()[0] if str(call.excinfo.value).strip() else call.excinfo.typename

    # Chrome version, read once from the running browser.
    browser = item.funcargs.get("driver") if hasattr(item, "funcargs") else None
    if browser is not None and RUN_INFO["chrome"] == "unknown":
        try:
            RUN_INFO["chrome"] = browser.capabilities.get("browserVersion", "unknown")
        except Exception:
            pass

    CASE_RESULTS.append({
        "id": test_id,
        "description": description,
        "passed": passed,
        "seconds": report.duration,
        "reason": reason,
    })

    # Used by the Description column of the results table.
    report.description = description

    # Attach the screenshot saved by test_gateway.py (TC01_PASS.png, TC01_FAIL.png, ...).
    # It is embedded in the report file itself, so the report is one self-contained file.
    if report_extras is not None and item.config.pluginmanager.hasplugin("html"):
        screenshot = os.path.join(os.path.dirname(str(item.fspath)), "screenshots", "{}_{}.png".format(test_id, "PASS" if passed else "FAIL"))
        if os.path.exists(screenshot):
            with open(screenshot, "rb") as image_file:
                encoded = base64.b64encode(image_file.read()).decode("ascii")
            report.extras = getattr(report, "extras", []) + [report_extras.png(encoded, name="Screenshot")]


@pytest.hookimpl(optionalhook=True)
def pytest_html_results_table_header(cells):
    """Add a Description column to the results table."""
    cells.insert(2, "<th>Description</th>")


@pytest.hookimpl(optionalhook=True)
def pytest_html_results_table_row(report, cells):
    """Fill the Description column for each row."""
    cells.insert(2, "<td>{}</td>".format(html.escape(getattr(report, "description", ""))))


@pytest.hookimpl(optionalhook=True)
def pytest_html_results_summary(prefix, summary, postfix, session):
    """Build the results overview shown at the top of the HTML report."""
    total = len(CASE_RESULTS)
    passed = sum(1 for result in CASE_RESULTS if result["passed"])
    failed = total - passed
    pass_rate = (passed * 100 / total) if total else 0
    run_seconds = time.time() - RUN_INFO["start"]
    longest = max([result["seconds"] for result in CASE_RESULTS] + [0.001])

    # Colours: green and red are used only for pass and fail, and always with
    # a symbol and a word, so the result never depends on colour alone.
    # Execution time is a single measure, so its bars use one blue.
    parts = ["""
<style>
  .gw { font: 14px/1.45 system-ui, -apple-system, "Segoe UI", sans-serif; color: #0b0b0b; margin: 8px 0 20px; max-width: 980px; }
  .gw h3 { font-size: 15px; font-weight: 600; margin: 22px 0 8px; }
  .gw-tiles { display: flex; flex-wrap: wrap; gap: 10px; }
  .gw-tile { flex: 1 1 130px; padding: 10px 14px; background: #fcfcfb; border: 1px solid #e1e0d9; border-radius: 6px; }
  .gw-tile span { display: block; color: #52514e; font-size: 13px; }
  .gw-tile strong { display: block; font-size: 26px; font-weight: 650; line-height: 1.2; font-variant-numeric: tabular-nums; }
  .gw-split { display: flex; gap: 2px; height: 14px; margin: 14px 0 6px; }
  .gw-split div { height: 14px; min-width: 4px; }
  .gw-split div:first-child { border-radius: 4px 0 0 4px; }
  .gw-split div:last-child { border-radius: 0 4px 4px 0; }
  .gw-split div:only-child { border-radius: 4px; }
  .gw-legend { color: #52514e; font-size: 13px; }
  .gw-legend i { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin: 0 5px 0 0; }
  .gw-legend span { margin-right: 18px; white-space: nowrap; }
  .gw-pass { color: #006300; font-weight: 600; white-space: nowrap; }
  .gw-fail { color: #d03b3b; font-weight: 600; white-space: nowrap; }
  .gw-times { border-collapse: collapse; width: 100%; font-variant-numeric: tabular-nums; }
  .gw-times td { padding: 4px 10px 4px 0; border-bottom: 1px solid #e1e0d9; vertical-align: middle; }
  .gw-times td.gw-id { width: 56px; font-weight: 600; }
  .gw-times td.gw-result { width: 70px; }
  .gw-times td.gw-desc { width: 300px; color: #52514e; font-size: 13px; }
  .gw-bar-row { display: flex; align-items: center; gap: 8px; }
  .gw-bar { height: 14px; min-width: 2px; background: #2a78d6; border-radius: 0 4px 4px 0; }
  .gw-times tr:hover .gw-bar { background: #1c5cab; }
  .gw-bar-value { color: #0b0b0b; font-size: 13px; white-space: nowrap; }
  .gw-failures { border-collapse: collapse; width: 100%; }
  .gw-failures th, .gw-failures td { text-align: left; padding: 6px 10px 6px 0; border-bottom: 1px solid #e1e0d9; vertical-align: top; }
  .gw-failures th { color: #52514e; font-size: 13px; font-weight: 600; }
  .gw-note { color: #52514e; font-size: 13px; margin: 6px 0 0; }
</style>
<div class="gw">
"""]

    # ---- (a) Summary of total tests, passes and failures ----
    parts.append('<div class="gw-tiles">')
    parts.append('<div class="gw-tile"><span>Test cases</span><strong>{}</strong></div>'.format(total))
    parts.append('<div class="gw-tile"><span>Passed</span><strong>{}</strong></div>'.format(passed))
    parts.append('<div class="gw-tile"><span>Failed</span><strong>{}</strong></div>'.format(failed))
    parts.append('<div class="gw-tile"><span>Pass rate</span><strong>{:.0f}%</strong></div>'.format(pass_rate))
    parts.append('<div class="gw-tile"><span>Total time</span><strong>{:.2f} s</strong></div>'.format(run_seconds))
    parts.append("</div>")

    # ---- (d) Visual element: pass/fail bar ----
    parts.append('<div class="gw-split" role="img" aria-label="{} passed, {} failed">'.format(passed, failed))
    if passed:
        parts.append('<div style="flex: {} 1 0; background: #0ca30c;" title="Passed: {}"></div>'.format(passed, passed))
    if failed:
        parts.append('<div style="flex: {} 1 0; background: #d03b3b;" title="Failed: {}"></div>'.format(failed, failed))
    parts.append("</div>")
    parts.append('<div class="gw-legend"><span><i style="background: #0ca30c;"></i>&#10003; Passed: {}</span><span><i style="background: #d03b3b;"></i>&#10007; Failed: {}</span></div>'.format(passed, failed))

    # ---- (c) Execution times, as a bar chart with one row per test case ----
    parts.append("<h3>Execution time per test case</h3>")
    parts.append('<table class="gw-times">')
    for result in CASE_RESULTS:
        width = max(result["seconds"] / longest * 100, 0.5)
        status = '<span class="gw-pass">&#10003; Pass</span>' if result["passed"] else '<span class="gw-fail">&#10007; Fail</span>'
        tooltip = html.escape("{}: {:.2f} s, {}".format(result["id"], result["seconds"], "passed" if result["passed"] else "failed"), quote=True)
        parts.append(
            '<tr title="{}"><td class="gw-id">{}</td><td class="gw-result">{}</td><td class="gw-desc">{}</td>'
            '<td><div class="gw-bar-row"><div class="gw-bar" style="width: {:.1f}%; max-width: calc(100% - 60px);"></div><span class="gw-bar-value">{:.2f} s</span></div></td></tr>'.format(
                tooltip, html.escape(result["id"]), status, html.escape(result["description"]), width, result["seconds"]))
    parts.append("</table>")
    parts.append('<p class="gw-note">Time for each test case to load the page, enter the values, check the result and save the screenshot. Total time also includes starting and closing the browser.</p>')

    # ---- (b) Failed test cases with a brief reason ----
    parts.append("<h3>Failed test cases</h3>")
    if failed == 0:
        parts.append('<p class="gw-note">None. All {} test cases passed.</p>'.format(total))
    else:
        parts.append('<table class="gw-failures"><tr><th>Test case</th><th>Description</th><th>Reason for failure</th></tr>')
        for result in CASE_RESULTS:
            if not result["passed"]:
                parts.append("<tr><td><strong>{}</strong></td><td>{}</td><td>{}</td></tr>".format(
                    html.escape(result["id"]), html.escape(result["description"]), html.escape(result["reason"])))
        parts.append("</table>")

    parts.append('<p class="gw-note">Run on {} with Python {} and Chrome {}. Application address: {}. Report generated {}.</p>'.format(
        html.escape(platform.platform()), html.escape(platform.python_version()), html.escape(RUN_INFO["chrome"]),
        html.escape(os.environ.get("APP_URL", "http://localhost/ai-gateway-project/index.html")),
        datetime.now().strftime("%d %b %Y, %H:%M:%S")))
    parts.append("</div>")

    prefix.append("\n".join(parts))


def pytest_sessionfinish(session, exitstatus):
    """On GitHub Actions, also show the results on the Summary page of the run."""
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY", "")
    if summary_file == "" or not CASE_RESULTS:
        return

    total = len(CASE_RESULTS)
    passed = sum(1 for result in CASE_RESULTS if result["passed"])
    lines = [
        "## Selenium test results",
        "",
        "| Test cases | Passed | Failed | Pass rate | Total time |",
        "|---|---|---|---|---|",
        "| {} | {} | {} | {:.0f}% | {:.2f} s |".format(total, passed, total - passed, passed * 100 / total, time.time() - RUN_INFO["start"]),
        "",
        "| Test case | Description | Result | Time | Reason for failure |",
        "|---|---|---|---|---|",
    ]
    for result in CASE_RESULTS:
        lines.append("| {} | {} | {} | {:.2f} s | {} |".format(
            result["id"], result["description"].replace("|", "/"),
            "✅ Pass" if result["passed"] else "❌ Fail", result["seconds"], result["reason"].replace("|", "/")))
    lines.append("")
    lines.append("Run on {} with Python {} and Chrome {}.".format(platform.platform(), platform.python_version(), RUN_INFO["chrome"]))
    lines.append("")

    with open(summary_file, "a", encoding="utf-8") as output:
        output.write("\n".join(lines) + "\n")
