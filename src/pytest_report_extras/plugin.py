import pytest
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
        default="h2",
        help="HTML tag for the test description. Accepted values: h1, h2, h3, p or pre.",
    )


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
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """ Override report generation. """
    pytest_html = item.config.pluginmanager.getplugin('html')
    outcome = yield
    report = outcome.get_result()
    extras = getattr(report, 'extras', [])

    # Is the test item using the 'report' fixtures?
    if not ("request" in item.funcargs and "report" in item.funcargs):
        return

    if report.when == 'call':
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
        xfail = hasattr(report, 'wasxfail')
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
            fx_report.step(target, f"Last screenshot")
            rows += utils.get_table_row_tag(
                fx_report.comments[-1],
                fx_report.images[-1],
                fx_report.sources[-1]
            )

        # Add screenshot for test failure/skip
        if failure and target is not None:
            if xfail or report.outcome == "failed":
                event = "failure"
            else:
                event = "skip"
            fx_report._fx_screenshots = "all"  # To force screenshot gathering
            fx_report.step(target, f"Last screenshot before {event}")
            rows += utils.get_table_row_tag(
                fx_report.comments[-1],
                fx_report.images[-1],
                fx_report.sources[-1],
                event
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
        report.extras = extras

'''
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    for item in terminalreporter.stats.items():
        passed = []
        failed = []
        xpassed = []
        xfailed = []
        skipped = []
        if item[0] == "passed":
            passed = item[1]
        if item[0] == "failed":
            failed = item[1]
        if item[0] == "skipped":
            skipped = item[1]
        if item[0] == "xpassed":
            xpassed = item[1]
        if item[0] == "xfailed":
            xfailed = item[1]
'''
