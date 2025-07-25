import importlib
import pathlib
import pytest
from . import decorators, utils
from .extras import Extras
from .status import Status


#
# Definition of test options
#
def pytest_addoption(parser):
    parser.addini(
        "extras_screenshots",
        type="string",
        default="all",
        help="The screenshots to include in the report. Accepted values: all, last, fail, none"
    )
    parser.addini(
        "extras_sources",
        type="bool",
        default=False,
        help="Whether to include webpage sources."
    )
    parser.addini(
        "extras_attachment_indent",
        type="int",
        default=4,
        help="The indent to use for attachments. Accepted value: a positive integer",
    )
    parser.addini(
        "extras_issue_link_pattern",
        type="string",
        default=None,
        help="The issue link pattern. Example: https://bugtracker.com/issues/{}",
    )
    parser.addini(
        "extras_tms_link_pattern",
        type="string",
        default=None,
        help="The test case link pattern. Example: https://tms.com/tests/{}",
    )
    parser.addini(
        "extras_links_column",
        type="string",
        default="all",
        help="The links type to show in the links columns. Accepted values: all, issue, tms, link, none",
    )
    parser.addini(
        "extras_title",
        type="string",
        default="Test Report",
        help="The test report title",
    )


#
# Fixtures for test options
#
@pytest.fixture(scope="session")
def _fx_screenshots(request):
    value = request.config.getini("extras_screenshots")
    if value in ("all", "last", "fail", "none"):
        return value
    else:
        return "all"


@pytest.fixture(scope="session")
def _fx_report_html(request):
    """ The folder storing the pytest-html report """
    return utils.get_folder(request.config.getoption("--html", default=None))


@pytest.fixture(scope="session")
def _fx_single_page(request):
    """ Whether to generate a single HTML page for pytest-html report """
    return request.config.getoption("--self-contained-html", default=False)


@pytest.fixture(scope="session")
def _fx_report_allure(request):
    """ Whether the allure-pytest plugin is being used """
    return request.config.getoption("--alluredir", default=None)


@pytest.fixture(scope="session")
def _fx_indent(request):
    """ The indent to use for attachments. """
    return request.config.getini("extras_attachment_indent")


@pytest.fixture(scope="session")
def _fx_sources(request):
    """ Whether to include webpage sources in the report. """
    return request.config.getini("extras_sources")


@pytest.fixture(scope='session')
def _fx_check(_fx_report_html, _fx_report_allure, _fx_single_page):
    """ Verifies preconditions before using this plugin. """
    utils.check_options(_fx_report_html, _fx_report_allure)


#
# Test fixture
#
@pytest.fixture(scope="function")
def report(_fx_report_html, _fx_single_page, _fx_screenshots, _fx_sources, _fx_indent, _fx_report_allure, _fx_check):
    return Extras(_fx_report_html, _fx_single_page, _fx_screenshots, _fx_sources, _fx_indent, _fx_report_allure)


#
# Hookers
#

# Global variables to store required fixtures to handle tms and issue markers
# Workaround for https://github.com/pytest-dev/pytest/issues/13101
fx_html = None
fx_allure = None
fx_tms_link_pattern = None
fx_issue_link_pattern = None
fx_links_column = "all"
fx_single_page = False
fx_title = ""


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Complete pytest-html report with extras and Allure report with attachments.
    """
    global fx_html, fx_allure, fx_single_page, fx_issue_link_pattern, fx_tms_link_pattern, fx_links_column

    outcome = yield
    pytest_html = item.config.pluginmanager.getplugin("html")
    report = outcome.get_result()
    extras = getattr(report, "extras", [])

    # Add links in decorators
    links = utils.get_markers_links(item, fx_issue_link_pattern, fx_tms_link_pattern)
    utils.add_links(item, extras, links, fx_html, fx_allure, fx_links_column)

    # Add extras for skipped or failed setup
    if (
        call.when == "setup" and
        (report.failed or report.skipped) and
        fx_html is not None and pytest_html is not None and
        "report" in item._fixtureinfo.argnames
    ):
        if report.failed:
            status = Status.ERROR
        else:  # report.skipped
            status = Status.SKIPPED
        header = decorators.get_header_rows(item, call, report, links, status)
        extras.append(pytest_html.extras.html(f'<table class="extras_header">{header}</table>'))

    # Exit if the test is not using the 'report' fixtures
    if not ("request" in item.funcargs and "report" in item.funcargs):
        report.extras = extras  # add links to the report before exiting
        return

    # Add extras for test execution
    if report.when == "call" and (fx_html is not None and pytest_html is not None):
        # Get test fixture values
        try:
            feature_request = item.funcargs["request"]
            fx_report = feature_request.getfixturevalue("report")
            fx_screenshots = feature_request.getfixturevalue("_fx_screenshots")
            target = fx_report.target
        except pytest.FixtureLookupError as error:
            utils.log_error(report, "Could not retrieve test fixtures", error)
            return

        # Set test status variables
        wasfailed = False
        wasxpassed = False
        wasxfailed = False
        wasskipped = False
        status = Status.UNKNOWN

        xfail = hasattr(report, "wasxfail")
        if report.failed:
            wasfailed = True
            status = Status.FAILED
        if report.skipped and not xfail:
            wasskipped = True
            status = Status.SKIPPED
        if report.skipped and xfail:
            wasxfailed = True
            status = Status.XFAILED
        if report.passed and xfail:
            wasxpassed = True
            status = Status.XPASSED
        if report.passed and not xfail:
            status = Status.PASSED

        # To check test failure/skip
        failure = wasfailed or wasxfailed or wasxpassed or wasskipped

        header = decorators.get_header_rows(item, call, report, links, status)

        if not utils.check_lists_length(report, fx_report):
            extras.append(pytest_html.extras.html(f'<table class="extras_header">{header}</table>'))
            return

        # Generate HTML code of the test execution steps to be added in the report
        steps = ""

        # Add steps in the report
        for i in range(len(fx_report.comments)):
            steps += decorators.get_step_row(
                fx_report.comments[i],
                fx_report.multimedia[i],
                fx_report.sources[i],
                fx_report.attachments[i],
                fx_single_page
            )

        clazz_row = None
        # Add screenshot for last step
        if fx_screenshots == "last" and failure is False and target is not None:
            try:
                fx_report._last_screenshot("Last screenshot", target)
            except Exception as error:
                clazz_row = "visibility_last_scr_error"
                utils.log_error(report, "Error gathering screenshot", error)
            steps += decorators.get_step_row(
                fx_report.comments[-1],
                fx_report.multimedia[-1],
                fx_report.sources[-1],
                fx_report.attachments[-1],
                fx_single_page,
                clazz_row
            )

        # Add screenshot for test failure/skip
        if fx_screenshots != "none" and failure and target is not None:
            comment = "Last screenshot"
            if status == Status.FAILED:
                comment += " before failure"
            if status == Status.XFAILED:
                comment += " before xfailure"
            if status == Status.SKIPPED:
                comment += " before skip"
            try:
                fx_report._last_screenshot(comment, target)
            except Exception as error:
                clazz_row = "visibility_last_scr_error"
                utils.log_error(report, "Error gathering screenshot", error)
            steps += decorators.get_step_row(
                fx_report.comments[-1],
                fx_report.multimedia[-1],
                fx_report.sources[-1],
                fx_report.attachments[-1],
                fx_single_page,
                clazz_row,
                f"extras_font extras_color_{status}"
            )

        # Add Execution title and horizontal line between the header and the steps table
        if len(steps) > 0:
            header += (
                '<tr class="visibility_execution">'
                '<td style="border: 0px"><span class="extras_title">Execution</span></td>'
                '<td class="extras_header_middle" style="border: 0px"></td>'
                '<td style="border: 0px"></td>'
                "</tr>"
            )
        extras.append(pytest_html.extras.html(f'<table class="extras_header">{header}</table>'))
        if len(steps) > 0 and header.count("</tr>") > 1:
            extras.append(pytest_html.extras.html('<hr class="extras_separator">'))

        # Append steps table
        if steps != "":
            extras.append(pytest_html.extras.html(f'<table style="width: 100%;">{steps}</table>'))

    report.extras = extras


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """
    Performs setup actions and sets global variables.
    """
    global fx_html, fx_allure, fx_issue_link_pattern, fx_tms_link_pattern, fx_single_page, fx_title, fx_links_column
    # Retrieve some options
    fx_html = utils.get_folder(config.getoption("--html", default=None))
    fx_allure = config.getoption("--alluredir", default=None)
    fx_single_page = config.getoption("--self-contained-html", default=False)
    fx_tms_link_pattern = config.getini("extras_tms_link_pattern")
    fx_issue_link_pattern = config.getini("extras_issue_link_pattern")
    fx_links_column = config.getini("extras_links_column")
    fx_title = config.getini("extras_title")

    # Add markers
    config.addinivalue_line("markers", "issue(keys, icon): The list of issue keys to add as links")
    config.addinivalue_line("markers", "tms(keys, icon): The list of test case keys to add as links")
    config.addinivalue_line("markers", "link(url, name, icon): The url to add as link")

    # Add default CSS file
    config_css = config.getoption("--css", default=[])
    resources_path = pathlib.Path(__file__).parent.joinpath("resources")
    style_css = pathlib.Path(resources_path, "style.css")
    if style_css.is_file():
        config_css.insert(0, style_css)


@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session):
    """ Create report asserts. """
    global fx_html, fx_single_page
    if fx_html is not None:
        utils.create_assets(fx_html, fx_single_page)


@pytest.hookimpl()
def pytest_sessionfinish(session, exitstatus):
    """ delete empty report subfolders. """
    global fx_html
    if fx_html is not None:
        utils.delete_empty_subfolders(fx_html)


if importlib.util.find_spec("pytest-html") is not None:
    def pytest_html_report_title(report):
        global fx_title
        report.title = fx_title
