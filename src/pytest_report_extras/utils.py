import base64
import html
import importlib
import os
import pathlib
import pytest
import shutil
import sys
import uuid
from typing import Literal
from typing import Optional


error_screenshot = None


#
# Auxiliary functions
#
def check_options(htmlpath, allurepath):
    """ Verifies if the --html or --alluredir option has been set. """
    if htmlpath is None and allurepath is None:
        message = ("It seems you are using pytest-report-extras plugin.\n"
                   "pytest-html or pytest-allure plugin is required.\n"
                   "'--html' or '--alluredir' option is missing.\n")
        print(message, file=sys.stderr)
        sys.exit(pytest.ExitCode.USAGE_ERROR)


def check_lists_length(report: pytest.TestReport, fx_extras) -> bool:
    """ Verifies if the comment, multimedia, page source and attachment lists have the same length """
    message = ('"multimedia", "comments", "sources", and "attachments" lists don\'t have the same length.\n'
               "Steps won't be logged for this test in pytest-html report.\n")
    if not (len(fx_extras.multimedia) == len(fx_extras.comments) == 
            len(fx_extras.sources) == len(fx_extras.attachments)):
        log_error(report, message)
        return False
    else:
        return True


def create_assets(report_html, single_page):
    """ Recreate report sub-folders. """
    global error_screenshot
    if report_html is None:
        return
    # Recreate report_folder
    folder = ""
    if report_html is not None and report_html != '':
        folder = f"{report_html}{os.sep}"
    try:
        # Create downloads folder
        shutil.rmtree(f"{folder}downloads", ignore_errors=True)
        pathlib.Path(f"{folder}downloads").mkdir(parents=True)
        # Get error image file
        resources_path = pathlib.Path(__file__).parent.joinpath("resources")
        error_img = pathlib.Path(resources_path, "error.png")
        if single_page:
            try:
                f = open(error_img, 'rb')
                data = f.read()
                f.close()
                error_screenshot = f"data:image/png;base64,{base64.b64encode(data).decode()}"
            except Exception:
                pass
            finally:
                return
        # Create other folders
        shutil.rmtree(f"{folder}sources", ignore_errors=True)
        pathlib.Path(f"{folder}sources").mkdir(parents=True)
        shutil.rmtree(f"{folder}videos", ignore_errors=True)
        pathlib.Path(f"{folder}videos").mkdir(parents=True)
        shutil.rmtree(f"{folder}images", ignore_errors=True)
        pathlib.Path(f"{folder}images").mkdir(parents=True)
        # Copy error.png to images folder
        shutil.copy(str(error_img), f"{folder}images")
        error_screenshot = f"images{os.sep}error.png"
    except OSError as error:
        message = ("Cannot create report sub-folders.\n"
                   "pytest-report-extras won't work properly.\n")
        print(message, repr(error), file=sys.stderr)


def get_folder(filepath) -> Optional[str]:
    """
    Returns the folder of a filepath.

    Args:
        filepath (str): The filepath.
    """
    folder = None
    if filepath is not None:
        folder = os.path.dirname(filepath)
    return folder


def escape_html(text, quote=False) -> Optional[str]:
    """ Escapes HTML characters in a text. """
    if text is None:
        return None
    return html.escape(str(text), quote)


#
# Screenshot related functions
#
def check_screenshot_target_type(target):
    """ Checks whether an object is an instance of WebDriver, WebElement, Page or Locator. """
    if importlib.util.find_spec("selenium") is not None:
        from selenium.webdriver.remote.webdriver import WebDriver
        from selenium.webdriver.remote.webelement import WebElement
        if isinstance(target, WebDriver) or isinstance(target, WebElement):
            return True

    if importlib.util.find_spec("playwright") is not None:
        from playwright.sync_api import Page
        from playwright.sync_api import Locator
        if isinstance(target, Page) or isinstance(target, Locator):
            return True
    return False


def get_screenshot(target, full_page=True, page_source=False) -> tuple[Optional[bytes], Optional[str]]:
    """
    Returns the screenshot in PNG format as bytes and the webpage source.

    Args:
        target (WebDriver | WebElement | Page | Locator): The target of the screenshot.
        full_page (bool): Whether to take a full-page screenshot if the target is an instance of WebDriver or Page.
        page_source (bool): Whether to gather the webpage source.

    Returns:
        The image as bytes and the webpage source if applicable.
    """
    image = None
    source = None

    if target is not None:
        if importlib.util.find_spec("selenium") is not None:
            from selenium.webdriver.remote.webdriver import WebDriver
            from selenium.webdriver.remote.webelement import WebElement
            if isinstance(target, WebElement) or isinstance(target, WebDriver):
                image, source = _get_selenium_screenshot(target, full_page, page_source)
    
        if importlib.util.find_spec("playwright") is not None:
            from playwright.sync_api import Page
            from playwright.sync_api import Locator
            if isinstance(target, Page) or isinstance(target, Locator):
                image, source = _get_playwright_screenshot(target, full_page, page_source)
    return image, source


def _get_selenium_screenshot(target, full_page=True, page_source=False) -> tuple[Optional[bytes], Optional[str]]:
    """
    Returns the screenshot in PNG format as bytes and the webpage source.

    Args:
        target (WebDriver | WebElement): The target of the screenshot.
        full_page (bool): Whether to take a full-page screenshot if the target is a WebDriver or WebElement instance.
        page_source (bool): Whether to gather the webpage source.

    Returns:
        The image as bytes and the webpage source if applicable.
    """
    from selenium.webdriver.chrome.webdriver import WebDriver as WebDriver_Chrome
    from selenium.webdriver.chromium.webdriver import ChromiumDriver as WebDriver_Chromium
    from selenium.webdriver.edge.webdriver import WebDriver as WebDriver_Edge
    from selenium.webdriver.remote.webelement import WebElement

    image = None
    source = None

    if isinstance(target, WebElement):
        image = target.screenshot_as_png
    else:
        if full_page is True:
            if hasattr(target, "get_full_page_screenshot_as_png"):
                image = target.get_full_page_screenshot_as_png()
            else:
                if type(target) in (WebDriver_Chrome, WebDriver_Chromium, WebDriver_Edge):
                    try:
                        image = _get_full_page_screenshot_chromium(target)
                    except Exception:
                        image = target.get_screenshot_as_png()
                else:
                    image = target.get_screenshot_as_png()
        else:
            image = target.get_screenshot_as_png()
        if page_source:
            source = target.page_source
    return image, source


def _get_playwright_screenshot(target, full_page=True, page_source=False) -> tuple[Optional[bytes], Optional[str]]:
    """
    Returns the screenshot in PNG format as bytes and the webpage source.

    Args:
        target (Page | Locator): The target of the screenshot.
        full_page (bool): Whether to take a full-page screenshot if the target is a Page or Locator instance.
        page_source (bool): Whether to gather the webpage source.

    Returns:
        The image as bytes and the webpage source if applicable.
    """
    from playwright.sync_api import Page

    image = None
    source = None

    if isinstance(target, Page):
        if target.is_closed():
            raise Exception("Page instance is closed")
        image = target.screenshot(full_page=full_page)
        if page_source:
            source = target.content()
    else:
        image = target.screenshot()
    return image, source


def _get_full_page_screenshot_chromium(driver) -> bytes:
    """ Returns the full-page screenshot in PNG format as bytes when using the Chromium WebDriver. """
    # get window size
    page_rect = driver.execute_cdp_cmd("Page.getLayoutMetrics", {})
    # parameters needed for full page screenshot
    # note we are setting the width and height of the viewport to screenshot, same as the site's content size
    screenshot_config = {
        "captureBeyondViewport": True,
        "fromSurface": True,
        "format": "png",
        "clip": {
            "x": 0,
            "y": 0,
            "width": page_rect["contentSize"]["width"],
            "height": page_rect["contentSize"]["height"],
            "scale": 1,
        },
    }
    # Dictionary with 1 key: data
    base_64_png = driver.execute_cdp_cmd("Page.captureScreenshot", screenshot_config)
    return base64.urlsafe_b64decode(base_64_png["data"])


#
# Persistence functions
#
def save_data_and_get_link(
    report_html: str,
    data: str | bytes,
    extension: Optional[str],
    folder: Literal["downloads", "images", "sources", "videos"]
) -> Optional[str]:
    """
    Saves data (as a string or bytes) in a file in the 'downloads' folder
    and returns its relative path to the HTML report folder.

    Args:
        report_html (str): The HTML report folder.
        data (str | bytes): The content in string or bytes to save.
        extension (str): The extension for the destination file.
        folder (str): The destination folder.

    Returns:
        The relative path to the HTML report folder of the created file.
    """
    if data in (None, ''):
        return None
    extension = '' if extension is None else '.' + extension 
    filename = str(uuid.uuid4()) + extension
    try:
        destination = f"{report_html}{os.sep}{folder}{os.sep}{filename}"
        if isinstance(data, bytes):
            f = open(destination, 'wb')
        else:
            f = open(destination, 'wt')
        f.write(data)
        f.close()
        return f"{folder}{os.sep}{filename}"
    except OSError as error:
        log_error(None, f"Error saving file to '{folder}' folder:", error)
        return None


def copy_file_and_get_link(
    report_html: str,
    filepath: str,
    extension: Optional[str],
    folder: Literal["downloads", "videos", "images"]
) -> Optional[str]:
    """
    Saves a copy of a file in a given folder
    and returns its relative path to the HTML report folder.

    Args:
        report_html (str): The HTML report folder.
        filepath (str): The name of the file to copy.
        extension (str): The extension for the destination file.
        folder (str): The destination folder.

    Returns:
        The relative path to the HTML report folder of the saved file.
    """
    if filepath in (None, ''):
        return None
    # Skip copy if file already present in destination folder
    if pathlib.Path(filepath).parent == pathlib.Path(pathlib.Path.cwd(), report_html, folder):
        return f"{folder}{os.sep}{pathlib.Path(filepath).name}"
    if extension is None and filepath.rfind('.') != -1:
        extension = filepath[filepath.rfind('.') + 1:]
    extension = '' if extension is None else '.' + extension 
    filename = str(uuid.uuid4()) + extension
    try:
        destination = f"{report_html}{os.sep}{folder}{os.sep}{filename}"
        shutil.copyfile(filepath, destination)
        return f"{folder}{os.sep}{filename}"
    except OSError as error:
        log_error(None, f"Error copying file '{filepath}' into folder '{folder}':", error)
        return None


#
# Marker functions
#
def add_marker_link(
    item: pytest.Item,
    extras,
    link_type: Literal["issues", "tms"],
    fx_link: Optional[str],
    fx_html: Optional[str],
    fx_allure: Optional[str]
):
    """
    Add links from @pytest.mark.issues and @pytest.mark.tms decorators.
    
    Args:
        item (pytest.Item): The test item.
        extras (List[pytest_html.extras.extra]): The test extras.
        link_type (str): The link type. Possible values: 'issues' and 'tms'.
        fx_link (str): The link pattern.
        fx_html (str): The report_html fixture.
        fx_allure (str): The report_allure fixture.
    """
    if fx_link is None or link_type not in ("issues", "tms"):
        return
    icons = {
        "issues": "&#128030;",
        "tms": "&#128203;",
    }
    icon = icons[link_type]
    pytest_html = item.config.pluginmanager.getplugin("html")
    marker = item.iter_markers(name=link_type)
    marker = next(marker, None)
    if marker is not None and len(marker.args) > 0:
        keys = marker.args[0].replace(' ', '').split(',')
        for key in keys:
            if key in (None, ''):
                continue            
            if fx_html is not None and pytest_html is not None:
                extras.append(pytest_html.extras.url(fx_link.replace("{}", key), name=f"{icon} {key}"))
            if fx_allure is not None and importlib.util.find_spec("allure") is not None:
                import allure
                from allure_commons.types import LinkType
                allure_link_type = LinkType.ISSUE if link_type == "issues" else LinkType.TEST_CASE
                allure.dynamic.link(fx_link.replace("{}", key), link_type=allure_link_type, name=key)


def add_marker_url(
    item: pytest.Item,
    extras,
    fx_html: Optional[str],
    fx_allure: Optional[str]
):
    """
    Add links from @pytest.mark.link decorator.
    
    Args:
        item (pytest.Item): The test item.
        extras (List[pytest_html.extras.extra]): The test extras.
        fx_html (str): The report_html fixture.
        fx_allure (str): The report_allure fixture.
    """
    icon = "&#127760;"
    pytest_html = item.config.pluginmanager.getplugin("html")
    for marker in item.iter_markers(name="link"):
        url = marker.args[0] if len(marker.args) > 0 else None
        name = marker.args[1] if len(marker.args) > 1 else None
        url = marker.kwargs.get("url", url)
        name = marker.kwargs.get("name", name)
        if url in (None, ''):
            continue            
        name = url if name is None else name
        if fx_html is not None and pytest_html is not None:
            extras.append(pytest_html.extras.url(url, name=f"{icon} {name}"))
        if fx_allure is not None and importlib.util.find_spec("allure") is not None:
            import allure
            from allure_commons.types import LinkType
            allure.dynamic.link(url, link_type=LinkType.LINK, name=name)


#
# Logger function
#
def log_error(
    report: Optional[pytest.TestReport],
    message: str,
    error: Optional[Exception] = None
):
    """
    Appends an error message in the stderr section of a test report.

    Args:
        report (pytest.TestReport): The pytest test report (optional).
        message (str): The message to log.
        error (Exception): The exception to log (optional).
    """
    message = f"{message}\n" if error is None else f"{message}\n{repr(error)}\n"
    if report is None:
        print(message, file=sys.stderr)
    else:
        found = False
        for i in range(len(report.sections)):
            if "stderr" in report.sections[i][0]:
                report.sections[i] = (
                    report.sections[i][0],
                    report.sections[i][1] + '\n' + message + '\n'
                )
                found = True
                break
        if not found:
            report.sections.append(("Captured stderr call", message))
