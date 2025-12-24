import importlib.util
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
# Auxiliary functions to read CLI and INI options
#
def _fx_screenshots(config):
    """ The screenshot strategy """
    value = config.getini("extras_screenshots")
    return value if value in ("all", "last", "fail", "none") else "all"


def _fx_html(config):
    """ The folder storing the pytest-html report """
    return utils.get_folder(config.getoption("--html", default=None))


def _fx_single_page(config):
    """ Whether to generate a single HTML page for pytest-html report """
    return config.getoption("--self-contained-html", default=False)


def _fx_allure(config):
    """ The folder storing the allure report """
    return config.getoption("--alluredir", default=None)


def _fx_indent(config):
    """ The indent to use for attachments. """
    return config.getini("extras_attachment_indent")


def _fx_sources(config):
    """ Whether to include webpage sources in the report. """
    return config.getini("extras_sources")


#
# Test fixture
#
@pytest.fixture(scope="function")
def report(request):
    return Extras(
        _fx_html(request.config),
        _fx_single_page(request.config),
        _fx_screenshots(request.config),
        _fx_sources(request.config),
        _fx_indent(request.config),
        _fx_allure(request.config)
    )


#
# Pytest Hooks
#
@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """
    Add markers and default CSS style file.
    """
    # Add markers
    config.addinivalue_line("markers", "issue(keys, icon): The list of issue keys to add as issue links")
    config.addinivalue_line("markers", "tms(keys, icon): The list of test case keys to add as tms links")
    config.addinivalue_line("markers", "link(url, name, icon): The url to add as web link")

    # Add default CSS file
    config_css = config.getoption("--css", default=[])
    resources_path = pathlib.Path(__file__).parent.joinpath("resources")
    style_css = pathlib.Path(resources_path, "style.css")
    if style_css.is_file():
        config_css.insert(0, style_css)


@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session):
    """ Create report assets. """
    config = session.config
    fx_html = _fx_html(config)
    fx_single_page = _fx_single_page(config)
    if fx_html is not None:
        utils.create_assets(fx_html, fx_single_page)


@pytest.hookimpl()
def pytest_sessionfinish(session, exitstatus):
    """ delete empty report subfolders. """
    config = session.config
    fx_html = _fx_html(config)
    fx_allure = _fx_allure(config)
    utils.delete_empty_subfolders(fx_html)
    utils.check_options(fx_html, fx_allure)


def pytest_collection_modifyitems(config, items):
    """ Add 'report' fixture for pytest-bdd tests. """
    fx_html = _fx_html(config)
    if (
        config.pluginmanager.has_plugin("pytest-bdd") and
        config.pluginmanager.has_plugin("html") and
        fx_html is not None
    ):
        for item in items:
            if (
                "_pytest_bdd_example" in item.fixturenames and
                "report" not in item.fixturenames
            ):
                item.fixturenames.append("report")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Complete pytest-html report with extras.
    """
    outcome = yield

    fx_allure = _fx_allure(item.config)
    fx_html = _fx_html(item.config)
    fx_issue_link_pattern = item.config.getini("extras_issue_link_pattern")
    fx_links_column = item.config.getini("extras_links_column")
    fx_screenshots = _fx_screenshots(item.config)
    fx_single_page = _fx_single_page(item.config)
    fx_tms_link_pattern = item.config.getini("extras_tms_link_pattern")

    pytest_html = item.config.pluginmanager.getplugin("html")
    report = outcome.get_result()
    extras = getattr(report, "extras", [])

    # Add links in decorators
    links = utils.get_all_markers_links(item, fx_issue_link_pattern, fx_tms_link_pattern)
    utils.add_links(item, extras, links, fx_html, fx_allure, fx_links_column)

    # Whether pytest-html is being used
    executing_pytest_html = fx_html is not None and pytest_html is not None

    # Add extras for skipped or failed setup
    if (
        report.when in ("setup", "teardown") and
        executing_pytest_html and
        (report.failed or report.skipped)
    ):
        if report.failed:
            status = Status.ERROR
        else:  # report.skipped
            status = Status.SKIPPED
        header = decorators.get_header_rows(item, call, report, links, status)
        extras.append(pytest_html.extras.html(f'<table class="extras_header">{header}</table>'))

    # If pytest-soft-assert is loaded, update test result status
    if call.when == "call" and item.config.pluginmanager.has_plugin("pytest_soft_assert"):
        try:
            soft = item.config.pluginmanager.getplugin("pytest_soft_assert")
            report = soft.update_test_status(report, item, call)
        except Exception:
            pass

    # Add extras for test execution
    if report.when == "call":
        # Get the 'report' fixture
        try:
            feature_request = item.funcargs["request"]
            fx_report: Extras = feature_request.getfixturevalue("report")
            target = fx_report.target
        except Exception:
            # The test doesn't have any fixture, so let's create a fake 'report' fixture
            fx_report: Extras = Extras(None, False, "none", False, 2, None)
            target = None

        # Set test status variables
        status = _calculate_status(report)
        failure = status in (Status.FAILED, Status.XFAILED, status.XPASSED, Status.SKIPPED)

        header = decorators.get_header_rows(item, call, report, links, status)
        steps = ""

        # Generate HTML code of the test execution steps to be added in the report
        if executing_pytest_html:

            # Verify integrity of 'report' fixture internal lists
            if not utils.check_lists_length(report, fx_report):
                extras.append(pytest_html.extras.html(f'<table class="extras_header">{header}</table>'))
                return

            # Add steps in the report
            for i in range(len(fx_report.comments)):
                steps += decorators.get_step_row(
                    fx_report.comments[i],
                    fx_report.multimedia[i],
                    fx_report.sources[i],
                    fx_report.attachments[i],
                    fx_single_page
                )

        clazz_visibility_row = None
        # Add screenshot for last step
        if fx_screenshots == "last" and failure is False and target is not None:
            try:
                fx_report._last_screenshot("Last screenshot", target)
            except Exception as error:
                clazz_visibility_row = "visibility_last_scr_error"
                utils.log_error(report, "Error gathering screenshot", error)
            if executing_pytest_html:
                steps += decorators.get_step_row(
                    fx_report.comments[-1],
                    fx_report.multimedia[-1],
                    fx_report.sources[-1],
                    fx_report.attachments[-1],
                    fx_single_page,
                    clazz_visibility_row
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
                clazz_visibility_row = "visibility_last_scr_error"
                utils.log_error(report, "Error gathering screenshot", error)
            if executing_pytest_html:
                steps += decorators.get_step_row(
                    fx_report.comments[-1],
                    fx_report.multimedia[-1],
                    fx_report.sources[-1],
                    fx_report.attachments[-1],
                    fx_single_page,
                    clazz_visibility_row,
                    f"extras_color_{status}"
                )

        # Let's put the steps and the header together
        if executing_pytest_html:
            # Add Execution title and horizontal line between the header and the steps table
            if len(steps) > 0:
                header += decorators.get_execution_row()
            extras.append(pytest_html.extras.html(f'<table class="extras_header">{header}</table>'))
            if len(steps) > 0 and header.count("</tr>") > 1:
                extras.append(pytest_html.extras.html('<hr class="extras_separator">'))
            # Append steps table
            if steps != "":
                extras.append(pytest_html.extras.html(f'<table style="width: 100%;">{steps}</table>'))

    report.extras = extras


#
# Pytest-html Hooks
#
if importlib.util.find_spec("html") and utils.is_package_installed("pytest-html"):
    def pytest_html_report_title(report):
        report.title = report.config.getini("extras_title")


#
# Auxiliary function
#
def _calculate_status(report: pytest.TestReport) -> Status:
    status = Status.UNKNOWN
    xfail = hasattr(report, "wasxfail")
    if report.failed:
        status = Status.FAILED
    if report.skipped and not xfail:
        status = Status.SKIPPED
    if report.skipped and xfail:
        status = Status.XFAILED
    if report.passed and xfail:
        status = Status.XPASSED
    if report.passed and not xfail:
        status = Status.PASSED

    return status
