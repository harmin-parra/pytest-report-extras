import pathlib
import pytest
import re
from . import utils
from .extras import Extras


#
# Definition of test options
#
def pytest_addoption(parser):
    parser.addini(
        "extras_screenshots",
        type="string",
        default="all",
        help="The screenshots to include in the report. Accepted values: all, last."
    )
    parser.addini(
        "extras_sources",
        type="bool",
        default=False,
        help="Whether to include webpage sources."
    )
    parser.addini(
        "extras_description_tag",
        type="string",
        default="pre",
        help="HTML tag for the test description. Accepted values: h1, h2, h3, p or pre.",
    )
    parser.addini(
        "extras_issue_link_pattern",
        type="string",
        default=None,
        help="The issue link pattern. Example: https://jira.com/issues/{}",
    )
    parser.addini(
        "extras_issue_key_pattern",
        type="string",
        default=None,
        help="The issue key pattern. Example: PROJ-\\d{1,4}",
    )


fx_issue_link = None
fx_issue_key = None


#
# Read test parameters
#
@pytest.fixture(scope='session')
def screenshots(request):
    value = request.config.getini("extras_screenshots")
    if value in ("all", "last"):
        return value
    else:
        return "all"


@pytest.fixture(scope='session')
def report_folder(request):
    """ The folder storing the pytest-html report """
    htmlpath = request.config.getoption("--html")
    return utils.get_folder(htmlpath)


@pytest.fixture(scope='session')
def report_allure(request):
    """ Whether the allure-pytest plugin is being used """
    return request.config.getoption("--alluredir", default=None) is not None


@pytest.fixture(scope='session')
def report_css(request):
    """ The filepath of the CSS to include in the report. """
    return request.config.getoption("--css")


@pytest.fixture(scope='session')
def description_tag(request):
    """ The HTML tag for the description of each test. """
    tag = request.config.getini("extras_description_tag")
    return tag if tag in ("h1", "h2", "h3", "p", "pre") else "h2"


@pytest.fixture(scope='session')
def sources(request):
    """ Whether to include webpage sources in the report. """
    return request.config.getini("extras_sources")


@pytest.fixture(scope='session')
def issue_link_pattern(request):
    """ The issue link pattern. """
    global fx_issue_link
    fx_issue_link = request.config.getini("extras_issue_link_pattern")
    return fx_issue_link


@pytest.fixture(scope='session')
def issue_key_pattern(request):
    """ The issue link pattern. """
    global fx_issue_key
    fx_issue_key = request.config.getini("extras_issue_key_pattern")
    return fx_issue_key


@pytest.fixture(scope='session')
def check_options(request, report_folder):
    """ Verifies preconditions before using this plugin. """
    utils.check_html_option(report_folder)
    utils.create_assets(report_folder)


#
# Test fixture
#
@pytest.fixture(scope='function')
def report(request, report_folder, screenshots, sources, report_allure, check_options):
    return Extras(report_folder, screenshots, sources, report_allure)


#
# Hookers
#
passed = 0
failed = 0
xfailed = 0
skipped = 0
xpassed = 0
error_setup = 0
error_teardown = 0


def pytest_sessionfinish(session, exitstatus):
    global skipped, failed, xfailed, passed, xpassed, error_setup, error_teardown
    if xpassed >= 0 and failed == 0 and error_setup == 0:
        session.exitstatus = 0
    if (xfailed + skipped + error_teardown + error_setup > 0) and failed == 0:
        session.exitstatus = 6


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    global skipped, failed, xfailed, passed, xpassed, error_setup, error_teardown
    global fx_issue_link, fx_issue_key

    """ Override report generation. """
    pytest_html = item.config.pluginmanager.getplugin('html')
    outcome = yield
    report = outcome.get_result()
    extras = getattr(report, 'extras', [])
    issues = []

    # Is the test item using the 'report' fixtures?
    # if not ("request" in item.funcargs and "report" in item.funcargs):
    #     return

    try:
        feature_request = item.funcargs['request']
        fx_issue_link = feature_request.getfixturevalue("issue_link_pattern")
        fx_issue_key = feature_request.getfixturevalue("issue_key_pattern")
    except:
        pass

    # Update status variables
    if call.when == 'setup':
        # For tests with the pytest.mark.skip fixture
        if (report.skipped and hasattr(call, 'excinfo')
                and call.excinfo is not None
                and call.excinfo.typename == 'Skipped'):
            issues = re.sub(r"[^\w-]", " ",  call.excinfo.value.msg).split()
            skipped += 1
        # For setup fixture
        if report.failed and call.excinfo is not None:
            error_setup += 1

    # Update status variables
    if call.when == 'teardown':
        if report.failed and call.excinfo is not None:
            error_teardown += 1

    if report.when == 'call':
        # Update status variables
        if report.failed:
            failed += 1
        if report.skipped and not hasattr(report, "wasxfail"):
            skipped += 1
        if report.skipped and hasattr(report, "wasxfail"):
            xfailed += 1
        if report.passed and hasattr(report, "wasxfail"):
            xpassed += 1
        if report.passed and not hasattr(report, "wasxfail"):
            passed += 1

        # Check for issue links to add
        # For tests with pytest.fail, pytest.xfail or pytest.skip call
        if (hasattr(call, 'excinfo')
                and call.excinfo is not None
                and (call.excinfo.typename in ('Failed', 'XFailed', 'Skipped'))):
            issues = re.sub(r"[^\w-]", " ",  call.excinfo.value.msg).split()
        # For tests with the pytest.mark.xfail fixture
        elif hasattr(report, 'wasxfail'):
            issues = re.sub(r"[^\w-]", " ",  report.wasxfail).split()

        # Is the test item using the 'report' fixtures?
        if "request" in item.funcargs and "report" in item.funcargs:

            # Get test fixture values
            feature_request = item.funcargs['request']
            fx_report = feature_request.getfixturevalue("report")
            fx_description_tag = feature_request.getfixturevalue("description_tag")
            fx_screenshots = feature_request.getfixturevalue("screenshots")
            # fx_issue_link = feature_request.getfixturevalue("issue_link_pattern")
            # fx_issue_key = feature_request.getfixturevalue("issue_key_pattern")
            target = fx_report.target
    
            # Append test description and execution exception trace, if any.
            description = item.function.__doc__ if hasattr(item, 'function') else None
            utils.append_header(call, report, extras, pytest_html, description, fx_description_tag)
    
            if not utils.check_lists_length(report, fx_report):
                return
    
            # Generate HTML code for the extras to be added in the report
            rows = ""   # The HTML table rows of the test report
    
            # To check test failure/skip
            xfail = hasattr(report, 'wasxfail')
            wasxpassed = xfail and report.wasxfail == "xpassed"
            wasxfailure = xfail and report.wasxfail == "xfailure"
            failure = xfail or report.outcome in ("failed", "skipped")
    
            # Add steps in the report
            for i in range(len(fx_report.images)):
                rows += utils.get_table_row_tag(
                    fx_report.comments[i],
                    fx_report.images[i],
                    fx_report.sources[i]
                )
    
            # Add screenshot for last step
            if fx_screenshots == "last" and failure is False and target is not None:
                fx_report._fx_screenshots = "all"  # To force screenshot gathering
                fx_report.step(f"Last screenshot", target)
                rows += utils.get_table_row_tag(
                    fx_report.comments[-1],
                    fx_report.images[-1],
                    fx_report.sources[-1]
                )
    
            # Add screenshot for test failure/skip
            if failure and target is not None:
                if report.outcome == "failed" or wasxpassed:
                    event_class = "failure"
                else:
                    event_class = "skip"
                if report.outcome == "failed" or wasxfailure or wasxpassed or (report.skipped and xfail):
                    event_label = "failure"
                else:
                    event_label = "skip"
                fx_report._fx_screenshots = "all"  # To force screenshot gathering
                fx_report.step(f"Last screenshot before {event_label}", target)
                rows += utils.get_table_row_tag(
                    fx_report.comments[-1],
                    fx_report.images[-1],
                    fx_report.sources[-1],
                    event_class
                )
    
            # Add horizontal line between the header and the comments/screenshots
            if len(extras) > 0 and len(rows) > 0:
                extras.append(pytest_html.extras.html(f'<hr class="extras_separator">'))
    
            # Append extras
            if rows != "":
                table = (
                    '<table style="width: 100%;">'
                    + rows +
                    "</table>"
                )
                extras.append(pytest_html.extras.html(table))

    # Identify issue patterns and add issue links to extras
    if fx_issue_key is not None and fx_issue_link is not None:
        for issue in issues:
            if re.match(rf"^{fx_issue_key}$", issue):
                extras.append(pytest_html.extras.url(fx_issue_link.replace("{}", issue), name=issue))

    report.extras = extras


@pytest.hookimpl(trylast=False)
def pytest_configure(config):
    # Add CSS file to --css request option for pytest-html
    # This code doesn't always run before pytest-html configuration
    report_css = config.getoption("--css")
    resources_path = pathlib.Path(__file__).parent.joinpath("resources")
    style_css = pathlib.Path(resources_path, "style.css")
    # report_css.insert(0, style_css)
    report_css.append(style_css)
