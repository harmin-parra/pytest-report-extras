import importlib
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
fx_html = None
fx_allure = None


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
def report_html(request):
    """ The folder storing the pytest-html report """
    global fx_html
    fx_html = utils.get_folder(request.config.getoption("--html", default=None))
    return fx_html


@pytest.fixture(scope='session')
def report_allure(request):
    """ Whether the allure-pytest plugin is being used """
    global fx_allure
    fx_allure = request.config.getoption("--alluredir", default=None) is not None
    return fx_allure


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
def check_options(request, report_html, report_allure):
    """ Verifies preconditions before using this plugin. """
    utils.check_options(report_html, report_allure)
    if report_html is not None:
        utils.create_assets(report_html)


#
# Test fixture
#
@pytest.fixture(scope='function')
def report(request, report_html, screenshots, sources, report_allure, check_options):
    return Extras(report_html, screenshots, sources, report_allure)


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
    if xpassed >= 0 and failed + skipped + error_setup + error_teardown == 0:
        session.exitstatus = 0
    if (xfailed + skipped + error_teardown + error_setup > 0) and failed == 0:
        session.exitstatus = 6


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    global skipped, failed, xfailed, passed, xpassed, error_setup, error_teardown
    global fx_issue_link, fx_issue_key, fx_html, fx_allure
    wasfailed = False
    wasxpassed = False
    wasxfailed = False
    wasskipped = False

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
        fx_html = feature_request.getfixturevalue("report_html")
        fx_allure = feature_request.getfixturevalue("report_allure")
        fx_issue_link = feature_request.getfixturevalue("issue_link_pattern")
        fx_issue_key = feature_request.getfixturevalue("issue_key_pattern")
    except:
        if call.when == "call":
            return

    # Update status variables
    if call.when == 'setup':
        # For tests with the pytest.mark.skip fixture
        if (report.skipped
                and hasattr(call, 'excinfo')
                and call.excinfo is not None
                and hasattr(call.excinfo.value, 'msg')):
            issues = re.sub(r"[^\w-]", " ",  call.excinfo.value.msg).split()
            wasskipped = True
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
            wasfailed = True
            failed += 1
        if report.skipped and not hasattr(report, "wasxfail"):
            wasskipped = True
            skipped += 1
        if report.skipped and hasattr(report, "wasxfail"):
            wasxfailed = True
            xfailed += 1
        if report.passed and hasattr(report, "wasxfail"):
            wasxpassed = True
            xpassed += 1
        if report.passed and not hasattr(report, "wasxfail"):
            passed += 1

        # Check for issue links to add
        # For tests with pytest.fail, pytest.xfail or pytest.skip call
        if (hasattr(call, 'excinfo')
                and call.excinfo is not None
                and hasattr(call.excinfo.value, 'msg')):
            issues = re.sub(r"[^\w-]", " ",  call.excinfo.value.msg).split()
        # For tests with the pytest.mark.xfail fixture
        elif hasattr(report, 'wasxfail'):
            issues = re.sub(r"[^\w-]", " ",  report.wasxfail).split()

        # Add extras to the pytest-html report
        # if the test item is using the 'report' fixtures and the pytest-html plugin
        if ("request" in item.funcargs and "report" in item.funcargs
                and fx_html is not None and pytest_html is not None):

            # Get test fixture values
            feature_request = item.funcargs['request']
            fx_report = feature_request.getfixturevalue("report")
            fx_description_tag = feature_request.getfixturevalue("description_tag")
            fx_screenshots = feature_request.getfixturevalue("screenshots")
            target = fx_report.target

            # Append test description and execution exception trace, if any.
            description = item.function.__doc__ if hasattr(item, 'function') else None
            utils.append_header(call, report, extras, pytest_html, description, fx_description_tag)

            if not utils.check_lists_length(report, fx_report):
                return

            # Generate HTML code for the extras to be added in the report
            rows = ""   # The HTML table rows of the test report

            # To check test failure/skip
            failure = wasfailed or wasxfailed or wasxpassed or wasskipped

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
                if wasfailed or wasxpassed:
                    event_class = "failure"
                else:
                    event_class = "skip"
                if wasfailed or wasxfailed or wasxpassed:
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

    # Identify issue patterns and add issue links to the report(s)
    if fx_issue_key is not None and fx_issue_link is not None:
        for issue in issues:
            if re.match(rf"^{fx_issue_key}$", issue):
                # Add extras to HTML report if pytest-html plugin is being used.
                if fx_html is not None and pytest_html is not None:
                    extras.append(pytest_html.extras.url(fx_issue_link.replace("{}", issue), name=issue))
                # Add extras to Allure report if allure-pytest plugin is being used.
                if fx_allure is not None and importlib.util.find_spec('allure') is not None:
                    import allure
                    from allure_commons.types import LinkType
                    allure.dynamic.link(fx_issue_link.replace("{}", issue), link_type=LinkType.LINK, name=issue)

    report.extras = extras


"""
@pytest.hookimpl(trylast=False)
def pytest_configure(config):
    # Add CSS file to --css request option for pytest-html
    # This code doesn't always run before pytest-html configuration
    try:
        report_css = config.getoption("--css", default=None)
        resources_path = pathlib.Path(__file__).parent.joinpath("resources")
        style_css = pathlib.Path(resources_path, "style.css")
        if report_css is not None:
            # report_css.insert(0, style_css)
            report_css.append(style_css)
    except:
        pass
"""
