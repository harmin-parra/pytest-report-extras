import base64
import html
import importlib
import os
import pathlib
import pytest
import shutil
import subprocess
import sys
import traceback
import uuid
from typing import List
# from . import Attachment


#
# Auxiliary functions to check options and fixtures
#
def check_options(htmlpath, allurepath):
    """ Verifies if the --html has been set by the user. """
    if htmlpath is None and allurepath is None:
        msg = ("It seems you are using pytest-report-extras plugin.\n"
               "pytest-html or pytest-allure plugin is required.\n"
               "'--html' or '--alluredir' option is missing.\n")
        print(msg, file=sys.stderr)
        sys.exit(pytest.ExitCode.USAGE_ERROR)


#def getini(config, name):
#    """ Workaround for bug https://github.com/pytest-dev/pytest/issues/11282 """
#    value = config.getini(name)
#    if not isinstance(value, str):
#        value = None
#    return value


def get_folder(filepath):
    """
    Returns the folder of a filepath.

    Args:
        filepath (str): The filepath.
    """
    folder = None
    if filepath is not None:
        folder = os.path.dirname(filepath)
    return folder


def check_lists_length(report, fx_extras):
    """ Verifies if the images, comments and page sources lists have the same lenght """
    message = ('"images", "comments" and "sources" lists don\'t have the same length.\n'
               "Screenshots won't be logged for this test in pytest-html report.\n"
               "images: {}, comments: {}, sources = {}")
    if not (len(fx_extras.images) == len(fx_extras.comments) == len(fx_extras.sources)):
        log_error_message(report, message.format(len(fx_extras.images), len(fx_extras.comments), len(fx_extras.sources)))
        return False
    else:
        return True


def create_assets(report_html):
    """ Recreate images and webpage sources folders. """
    if report_html is None:
        return
    # Recreate report_folder
    folder = ""
    if report_html is not None and report_html != '':
        folder = f"{report_html}{os.sep}"
    # Create page sources folder
    shutil.rmtree(f"{folder}sources", ignore_errors=True)
    pathlib.Path(f"{folder}sources").mkdir(parents=True)
    # Create images folder
    shutil.rmtree(f"{folder}images", ignore_errors=True)
    pathlib.Path(f"{folder}images").mkdir(parents=True)
    # Create downloads folder
    shutil.rmtree(f"{folder}downloads", ignore_errors=True)
    pathlib.Path(f"{folder}downloads").mkdir(parents=True)
    # Copy error.png to images folder
    resources_path = pathlib.Path(__file__).parent.joinpath("resources")
    error_img = pathlib.Path(resources_path, "error.png")
    shutil.copy(str(error_img), f"{folder}images")


#
# Persistence functions
#
def get_full_page_screenshot_chromium(driver):
    # get window size
    page_rect = driver.execute_cdp_cmd("Page.getLayoutMetrics", {})
    # parameters needed for full page screenshot
    # note we are setting the width and height of the viewport to screenshot, same as the site's content size
    screenshot_config = {
        'captureBeyondViewport': True,
        'fromSurface': True,
        'format': "png",
        'clip': {
            'x': 0,
            'y': 0,
            'width': page_rect['contentSize']['width'],
            'height': page_rect['contentSize']['height'],
            'scale': 1,
        },
    }
    # Dictionary with 1 key: data
    base_64_png = driver.execute_cdp_cmd("Page.captureScreenshot", screenshot_config)
    return base64.urlsafe_b64decode(base_64_png['data'])


def get_screenshot(target, full_page=True, page_source=False):
    image = None
    source = None

    if target is not None:
        if importlib.util.find_spec('selenium') is not None:
            from selenium.webdriver.remote.webdriver import WebDriver
            from selenium.webdriver.remote.webelement import WebElement
            if isinstance(target, WebElement) or isinstance(target, WebDriver):
                image, source = _get_selenium_screenshot(target, full_page, page_source)

        if importlib.util.find_spec('playwright') is not None:
            from playwright.sync_api import Page
            from playwright.sync_api import Locator
            if isinstance(target, Page) or isinstance(target, Locator):
                image, source = _get_playwright_screenshot(target, full_page, page_source)
    
    return image, source


def _get_selenium_screenshot(target, full_page=True, page_source=False):
    """
    Returns the screenshot in PNG format as bytes and the HTML source code.
        target (WebDriver | WebElement): The target of the screenshot.
        full_page (bool): Whether to take a full-page screenshot if the target is a Page instance.
                          Defaults to True.
    """
    image = None
    source = None

    if importlib.util.find_spec('selenium') is not None:
        from selenium.webdriver.chrome.webdriver import WebDriver as WebDriver_Chrome
        from selenium.webdriver.chromium.webdriver import ChromiumDriver as WebDriver_Chromium
        from selenium.webdriver.edge.webdriver import WebDriver as WebDriver_Edge
        from selenium.webdriver.remote.webelement import WebElement
    else:
        print("Selenium module is not installed.", file=sys.stderr)
        return image, source

    if isinstance(target, WebElement):
        image = target.screenshot_as_png
    else:
        if full_page is True:
            if hasattr(target, "get_full_page_screenshot_as_png"):
                image = target.get_full_page_screenshot_as_png()
            else:
                if type(target) in (WebDriver_Chrome, WebDriver_Chromium, WebDriver_Edge):
                    try:
                        image = get_full_page_screenshot_chromium(target)
                    except:
                        image = target.get_screenshot_as_png()
                else:
                    image = target.get_screenshot_as_png()
        else:
            image = target.get_screenshot_as_png()
        if page_source:
            source = target.page_source
    return image, source


def _get_playwright_screenshot(target, full_page=True, page_source=False):
    """
    Returns a screenshot in PNG format as bytes.
        target (Page | Locator): The target of the screenshot.
        full_page (bool): Whether to take a full-page screenshot if the target is a Page instance.
                          Defaults to True.
    """
    image = None
    source = None

    if importlib.util.find_spec('playwright') is not None:
        from playwright.sync_api import Page
        from playwright.sync_api import Locator
        assert isinstance(target, Page) or isinstance(target, Locator)
    else:
        print("Playwright module is not installed.", file=sys.stderr)
        return image, source

    if isinstance(target, Page):
        image = target.screenshot(full_page=full_page)
        if page_source:
            source = target.content()
    else:
        image = target.screenshot()

    return image, source


def get_image_link(report_html, index, image):
    """
    Saves an image in the 'images' folder and returns its relative path to the report folder.
    
    Args:
        report_html (str): The report folder.
        index (int): The file name suffix.
        image (bytes) : The image to save.
    """
    if image is None:
        return None
    link = f"images{os.sep}image-{index}.png"
    folder = ""
    if report_html is not None and report_html != '':
        folder = f"{report_html}{os.sep}"
    filename = folder + link
    try:
        f = open(filename, 'wb')
        f.write(image)
        f.close()
    except Exception as err:
        trace = traceback.format_exc()
        link = f"images{os.sep}error.png"
        print(f"{str(err)}\n\n{trace}", file=sys.stderr)
    finally:
        return link


def get_source_link(report_html, index, source):
    """
    Saves a webpage source in the 'sources' folder and returns its relative path to the report folder.
    Args:
        report_html (str): The report folder.
        index (int): The file name suffix.
        source (str) : The webpage source to save.
    """
    if source is None:
        return None
    link = f"sources{os.sep}page-{index}.txt"
    folder = ""
    if report_html is not None and report_html != '':
        folder = f"{report_html}{os.sep}"
    filename = folder + link
    try:
        f = open(filename, 'w', encoding="utf-8")
        f.write(source)
        f.close()
    except Exception as err:
        trace = traceback.format_exc()
        link = None
        print(f"{str(err)}\n\n{trace}", file=sys.stderr)
    finally:
        return link


def get_download_link(report_html, target: str | bytes = None):
    """
    Saves a file or bytes in the 'downloads' folder and returns its relative path to the report folder.

    Args:
        report_html (str): The report folder.
        target (file | bytes): The name of the file or the bytes to save.
        image (buyes) : The image to save.
    """
    if target is None:
        return None
    filename = str(uuid.uuid4())
    try:
        destination = f"{report_html}{os.sep}downloads{os.sep}{filename}"
        if isinstance(target, str):
            subprocess.run(["cp", target, destination]).check_returncode()
        else:  # bytes
            f = open(destination, 'wb')
            f.write(target)
            f.close()            
        return f"downloads{os.sep}{filename}"
    except:
        raise


#
# Auxiliary functions for the report generation
#
def append_header(call, report, extras, pytest_html,
                  description, description_tag):
    """
    Appends the description and the test execution exception trace, if any, to a test report.

    Args:
        description (str): The test function docstring.
        description_tag (str): The HTML tag to use.
    """
    clazz = "extras_exception"
    # Append description
    if description is not None:
        description = escape_html(description).strip().replace('\n', "<br>")
        description = description.strip().replace('\n', "<br>")
        extras.append(pytest_html.extras.html(f'<{description_tag} class="extras_description">{description}</{description_tag}>'))

    # Catch explicit pytest.fail and pytest.skip calls
    if (
        hasattr(call, 'excinfo') and
        call.excinfo is not None and
        call.excinfo.typename in ('Failed', 'Skipped') and
        hasattr(call.excinfo, "value") and
        hasattr(call.excinfo.value, "msg")
    ):
        extras.append(pytest_html.extras.html(
            "<pre>"
            f'<span class="{clazz}">{escape_html(call.excinfo.typename)}</span><br>'
            f"reason = {escape_html(call.excinfo.value.msg)}"
            "</pre>"
            )
        )
    # Catch XFailed tests
    if report.skipped and hasattr(report, 'wasxfail'):
        extras.append(pytest_html.extras.html(
            "<pre>"
            f'<span class="{clazz}">XFailed</span><br>'
            f"reason = {escape_html(report.wasxfail)}"
            "</pre>"
            )
        )
    # Catch XPassed tests
    if report.passed and hasattr(report, 'wasxfail'):
        extras.append(pytest_html.extras.html(
            "<pre>"
            f'<span class="{clazz}">XPassed</span><br>'
            f"reason = {escape_html(report.wasxfail)}"
            "</pre>"
            )
        )
    # Catch explicit pytest.xfail calls and runtime exceptions in failed tests
    if (
        hasattr(call, 'excinfo') and
        call.excinfo is not None and
        call.excinfo.typename not in ('Failed', 'Skipped') and
        hasattr(call.excinfo, '_excinfo') and
        call.excinfo._excinfo is not None and
        isinstance(call.excinfo._excinfo, tuple) and
        len(call.excinfo._excinfo) > 1
    ):
        extras.append(pytest_html.extras.html(
            "<pre>"
            f'<span class="{clazz}">Exception:</span><br>'
            f"{escape_html(call.excinfo.typename)}<br>"
            f"{escape_html(call.excinfo._excinfo[1])}"
            "</pre>"
            )
        )
    report.extras = extras


def escape_html(text, quote=False) -> str:
    """ Escapes HTML characters in a text. """
    if text is None:
        return ""
    return html.escape(str(text), quote)


def get_table_row_tag(comment, image, source, clazz_comment="comment") -> str:
    """
    Returns the HTML table row of a test step.

    Args:
        comment (str): The comment of the test step.
        image (str): The screenshot anchor element.
        source (str): The page source anchor element.
        clazz_comment (str): The CSS class to apply to the comment table cell.

    Returns:
        str: The <tr> element.
    """
    clazz = f"extras_{clazz_comment}"
    if isinstance(comment, str):
        comment = decorate_label(comment, clazz)
    else:
        comment = ""
    if image is not None:
        image = decorate_image(image)
        if source is not None:
            source = decorate_page_source(source)
            return (
                f"<tr>"
                f"<td>{comment}</td>"
                f'<td class="extras_td"><div class="extras_td_div">{image}<br>{source}</div></td>'
                f"</tr>"
            )
        else:
            return (
                f"<tr>"
                f"<td>{comment}</td>"
                f'<td class="extras_td"><div class="extras_td_div">{image}</div></td>'
                "</tr>"
            )
    else:
        return (
            f"<tr>"
            f'<td colspan="2">{comment}</td>'
            f"</tr>"
        )


def decorate_label(label, clazz) -> str:
    """
    Applies a CSS style to a text.

    Args:
        label (str): The text to decorate.
        clazz (str): The CSS class to apply.

    Returns:
        The <span> element decorated with the CSS class.
    """
    return f'<span class="{clazz}">{label}</span>'


# def decorate_anchors(image, source):
#     if image is None:
#         return ''
#     """ Applies CSS style to a screenshot and page source anchor elements. """
#     image = decorate_image(image)
#     if source is not None:
#         source = decorate_page_source(source)
#         return f'<div class="extras_div">{image}<br>{source}</div>'
#     else:
#         return image


def decorate_image(uri) -> str:
    """ Applies CSS class to an image anchor element. """
    clazz = "extras_image"
    if uri is None:
        return ""
    return f'<a href="{uri}" target="_blank"><img src ="{uri}" class="{clazz}"></a>'


def decorate_image_from_file(filename) -> str:
    return decorate_image(filename)


def decorate_image_from_bytes(data: bytes, mime: str) -> str:
    uri = None
    if data is not None:
        try:
            uri = f"data:{mime};base64,{base64.b64encode(data)}"
        except:
            pass
    return decorate_image(uri)


def decorate_page_source(filename) -> str:
    """ Applies CSS class to a page source anchor element. """
    if filename is None:
        return ""
    clazz = "extras_page_src"
    return f'<a href="{filename}" target="_blank" class="{clazz}">[page source]</a>'


def decorate_uri(uri: str) -> str:
    """ Applies CSS class to a uri anchor element. """
    if uri is None or uri == '':
        return ""
    if uri.startswith("downloads"):
        return f'<a href="{uri}" target="_blank">{pathlib.Path(uri).name}</a>'
    else:
        return f'<a href="{uri}" target="_blank">{uri}</a>'


def decorate_uri_list(uris: List[str]) -> str:
    """ Applies CSS class to a list of uri attachment. """
    links = ""
    for uri in uris:
        if uri is not None and uri != '':
            links += decorate_uri(uri) + "<br>"
    return links


def decorate_attachment(attachment) -> str:
    """ Applies CSS class to an attachment. """
    clazz1 = "extras_pre"
    clazz2 = "extras_iframe"
    if attachment.inner_html is None:
        if attachment.body in (None, ""):
            return ""
        else:
            return f'<pre class="{clazz1}">{escape_html(attachment.body)}</pre>'
    else:
        if attachment.mime == "text/html":
            return f'<iframe class="{clazz2}" src="{attachment.inner_html}"></iframe>'
        if attachment.mime.startswith("image"):
            return attachment.inner_html
        else:
            return f'<pre class="{clazz1}">{attachment.inner_html}</pre>'


def log_error_message(report, message):
    """ Appends error message in stderr section of a test report. """
    try:
        i = -1
        for x in range(len(report.sections)):
            if "stderr call" in report.sections[x][0]:
                i = x
                break
        if i != -1:
            report.sections[i] = (
                report.sections[i][0],
                report.sections[i][1] + '\n' + message + '\n'
            )
        else:
            report.sections.append(('Captured stderr call', message))
    except:
        pass
