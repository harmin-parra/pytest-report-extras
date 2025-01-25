import importlib
import pathlib
import pytest
from . import decorators
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
        help="The HTML tag for the test description. Accepted values: h1, h2, h3, p or pre.",
    )
    parser.addini(
        "extras_attachment_indent",
        type="string",
        default="4",
        help="The indent to use for attachments. Accepted value: a positive integer",
    )
    parser.addini(
        "extras_issue_link_pattern",
        type="string",
        default=None,
        help="The issue link pattern. Example: https://jira.com/issues/{}",
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
def report_html(request):
    """ The folder storing the pytest-html report """
    return utils.get_folder(request.config.getoption("--html", default=None))


@pytest.fixture(scope='session')
def single_page(request):
    """ Whether to generate a single HTML page for pytest-html report """
    return request.config.getoption("--self-contained-html", default=False)


@pytest.fixture(scope='session')
def report_allure(request):
    """ Whether the allure-pytest plugin is being used """
    return request.config.getoption("--alluredir", default=None)


@pytest.fixture(scope='session')
def report_css(request):
    """ The filepath of the CSS to include in the report. """
    return request.config.getoption("--css")


@pytest.fixture(scope='session')
def description_tag(request):
    """ The HTML tag for the description of each test. """
    tag = request.config.getini("extras_description_tag")
    return tag if tag in ("h1", "h2", "h3", "p", "pre") else "pre"


@pytest.fixture(scope='session')
def indent(request):
    """ The indent to use for attachments. """
    indent = request.config.getini("extras_attachment_indent")
    try:
        return int(indent)
    except ValueError:
        return 4


@pytest.fixture(scope='session')
def sources(request):
    """ Whether to include webpage sources in the report. """
    return request.config.getini("extras_sources")


@pytest.fixture(scope='session')
def issue_link_pattern(request):
    """ The issue link pattern. """
    return request.config.getini("extras_issue_link_pattern")


@pytest.fixture(scope='session')
def check_options(report_html, report_allure, single_page):
    """ Verifies preconditions and create assets before using this plugin. """
    utils.check_options(report_html, report_allure)
    if report_html is not None:
        utils.create_assets(report_html, single_page)


#
# Test fixture
#
@pytest.fixture(scope='function')
def report(report_html, single_page, screenshots, sources, report_allure, indent, check_options):
    return Extras(report_html, single_page, screenshots, sources, report_allure, indent)


#
# Hookers
#

# Global variables to store key fixtures to handle issue links in setup failures
# Workaround for bug https://github.com/pytest-dev/pytest/issues/13101
fx_html = None
fx_allure = None
fx_issue_link = None


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Complete pytest-html report with extras and Allure report with attachments.
    """
    global fx_html, fx_allure, fx_issue_link
    wasfailed = False
    wasxpassed = False
    wasxfailed = False
    wasskipped = False

    outcome = yield
    pytest_html = item.config.pluginmanager.getplugin('html')
    report = outcome.get_result()
    extras = getattr(report, 'extras', [])

    # Add issues in marker as links
    marker = item.iter_markers(name="issues")
    marker = next(marker, None)
    if marker is not None and len(marker.args) > 0 and fx_issue_link is not None:
        issues = marker.args[0].replace(' ', '').split(',')
        for issue in issues:
            if issue in (None, ''):
                continue            
            if fx_html is not None and pytest_html is not None:
                extras.append(pytest_html.extras.url(fx_issue_link.replace("{}", issue), name=issue))
            if fx_allure is not None and importlib.util.find_spec('allure') is not None:
                import allure
                from allure_commons.types import LinkType
                allure.dynamic.link(fx_issue_link.replace("{}", issue), link_type=LinkType.LINK, name=issue)

    # Exit if the test is not using the 'report' fixtures
    if not ("request" in item.funcargs and "report" in item.funcargs):
        report.extras = extras
        return

    if report.when == 'call':
        xfail = hasattr(report, "wasxfail")
        # Update status variables
        if report.failed:
            wasfailed = True
        if report.skipped and not xfail:
            wasskipped = True
        if report.skipped and xfail:
            wasxfailed = True
        if report.passed and xfail:
            wasxpassed = True

        # Add extras to the pytest-html report
        # if the test item is using the 'report' fixtures and the pytest-html plugin
        if ("request" in item.funcargs and "report" in item.funcargs
                and fx_html is not None and pytest_html is not None):

            # Get test fixture values
            try:
                feature_request = item.funcargs['request']
                fx_report = feature_request.getfixturevalue("report")
                fx_single_page = feature_request.getfixturevalue("single_page")
                fx_description_tag = feature_request.getfixturevalue("description_tag")
                fx_screenshots = feature_request.getfixturevalue("screenshots")
                # fx_html = feature_request.getfixturevalue("report_html")
                # fx_allure = feature_request.getfixturevalue("report_allure")
                # fx_issue_link = feature_request.getfixturevalue("issue_link_pattern")
                target = fx_report.target
            except Exception as error:
                utils.log_error(report, "Could not retrieve test fixtures", error)
                return

            # Append test description and execution exception trace, if any.
            description = item.function.__doc__ if hasattr(item, 'function') else None
            decorators.append_header(call, report, extras, pytest_html, description, fx_description_tag)

            if not utils.check_lists_length(report, fx_report):
                return

            # Generate HTML code for the extras to be added in the report
            rows = ""   # The HTML table rows of the test report

            # To check test failure/skip
            failure = wasfailed or wasxfailed or wasxpassed or wasskipped

            # Add steps in the report
            for i in range(len(fx_report.images)):
                rows += decorators.get_table_row_tag(
                    fx_report.comments[i],
                    fx_report.images[i],
                    fx_report.sources[i],
                    fx_report.attachments[i],
                    fx_single_page
                )

            # Add screenshot for last step
            if fx_screenshots == "last" and failure is False and target is not None:
                fx_report._fx_screenshots = "all"  # To force screenshot gathering
                fx_report.screenshot(f"Last screenshot", target)
                rows += decorators.get_table_row_tag(
                    fx_report.comments[-1],
                    fx_report.images[-1],
                    fx_report.sources[-1],
                    fx_report.attachments[-1],
                    fx_single_page
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
                fx_report.screenshot(f"Last screenshot before {event_label}", target)
                rows += decorators.get_table_row_tag(
                    fx_report.comments[-1],
                    fx_report.images[-1],
                    fx_report.sources[-1],
                    fx_report.attachments[-1],
                    fx_single_page,
                    f"extras_{event_class}"
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

            # Add links to the report(s)
            for link in fx_report.links:
                if fx_html is not None and pytest_html is not None:
                    if link[1] not in (None, ""):
                        extras.append(pytest_html.extras.url(link[0], name=link[1]))
                    else:
                        extras.append(pytest_html.extras.url(link[0], name=link[0]))
                if fx_allure is not None and importlib.util.find_spec('allure') is not None:
                    import allure
                    if link[1] not in (None, ""):
                        allure.dynamic.link(link[0], name=link[1])
                    else:
                        allure.dynamic.link(link[0], name=link[0])

    report.extras = extras


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """ 
    Add CSS file to --css request option for pytest-html
    Set global variables.
    """
    global fx_html, fx_allure, fx_issue_link
    fx_html = utils.get_folder(config.getoption("--html", default=None))
    fx_allure = config.getoption("--alluredir", default=None)
    fx_issue_link = config.getini("extras_issue_link_pattern")
    config.addinivalue_line("markers", "issues(keys): The list of issue keys to add as links")

    try:
        report_css = config.getoption("--css", default=[])
        resources_path = pathlib.Path(__file__).parent.joinpath("resources")
        style_css = pathlib.Path(resources_path, "style.css")
        report_css.insert(0, style_css)
    except:
        pass
