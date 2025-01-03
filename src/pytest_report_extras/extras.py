import base64
import html
import importlib
import warnings
from typing import Dict
from typing import List
from . import utils
from .attachment import Attachment
from .attachment import Mime


deprecation_msg = """

report.step(....) is deprecated and will be removed in the next major version release

Please use:
    report.screenshot: To add steps with screenshots.
    report.attach: To add steps with attachments.

Examples:
report.screenshot(
    comment="comment",
    target=<WebDriver>
)
report.attach(
    comment="comment",
    body="<XML string>",
    mime=report.Mime.application_xml
)
report.attach(
    comment="comment",
    source="/path/to/JSON file",
    mime=report.Mime.application_json
)
"""


# Counter used for image and page source files naming
count = 0


def counter() -> int:
    """ Returns a suffix used for image and webpage source file naming """
    global count
    count += 1
    return count


# Deprecated attachment class
class CodeBlockText(Attachment):
    pass


class Extras:
    """
    Class to hold pytest-html 'extras' to be added for each test in the HTML report.
    """

    def __init__(self, report_html, fx_screenshots, fx_sources, report_allure, indent):
        """
        Args:
            report_html (str): The 'report_html' fixture.
            fx_screenshots (str): The 'screenshots' fixture.
            fx_sources (bool): The 'sources' fixture.
            report_allure (str): The 'report_allure' fixture.
            indent: The 'indent' fixture.
        """
        self.images = []
        self.sources = []
        self.comments = []
        self.links = []
        self.target = None
        self._fx_screenshots = fx_screenshots
        self._fx_sources = fx_sources
        self._html = report_html
        self._allure = report_allure
        self._indent = indent
        self.Mime = Mime

    def screenshot(
            self,
            comment: str,
            target = None,
            full_page: bool = True,
            page_source: bool = False,
            escape_html: bool = False
    ):
        """
        Adds a step with a screenshot in the report.
        The screenshot is saved in <report_html>/screenshots folder.
        The webpage source is saved in <report_html>/sources folder.

        Args:
            comment (str): The comment of the test step.
            target (WebDriver | WebElement | Page | Locator): The target of the screenshot.
            full_page (bool): Whether to take a full-page screenshot.
            page_source (bool): Whether to include the page source. Overrides the global `sources` fixture.
            escape_html (bool): Whether to escape HTML characters in the comment.
        """
        if target is not None:
            if importlib.util.find_spec('selenium') is not None:
                from selenium.webdriver.remote.webdriver import WebDriver
                if isinstance(target, WebDriver) and self.target is None:
                    self.target = target

            if importlib.util.find_spec('playwright') is not None:
                from playwright.sync_api import Page
                if isinstance(target, Page) and self.target is None:
                    self.target = target

        if self._fx_screenshots == "last" and target is not None:
            return

        # Get the 3 parts of the test step: image, comment and source
        image, source = utils.get_screenshot(target, full_page, self._fx_sources or page_source)
        comment = "" if comment is None else comment
        comment = html.escape(comment, quote=True) if escape_html else comment

        # Add extras to Allure report if allure-pytest plugin is being used.
        if self._allure and importlib.util.find_spec('allure') is not None:
            import allure
            if image is not None:
                allure.attach(image, name=comment, attachment_type=allure.attachment_type.PNG)
                # Attach the webpage source
                if source is not None:
                    allure.attach(source, name="page source", attachment_type=allure.attachment_type.TEXT)

        # Add extras to pytest-html report if pytest-html plugin is being used.
        if self._html:
            self._save_screenshot(image, source)
            self.comments.append(comment)

    def attach(
            self,
            comment: str,
            body: str = None,
            source: str = None,
            mime: str = None,
            csv_delimiter=',',
            escape_html: bool = False
    ):
        """
        Adds a step in the pytest-html report: screenshot, comment and webpage source.
        The screenshot is saved in <report_html>/screenshots folder.
        The webpage source is saved in <report_html>/sources folder.
        The 'body' and 'source' parameters are exclusive.

        Args:
            comment (str): The comment of the test step.
            body (str | Dict | List[str]): The content/body of the attachment.
                Can be of type 'Dict' for JSON mime type.
                Can be of type 'List[str]' for uri-list mime type.
            source (str): The filepath of the source to attach.
            mime (str): The attachment mime type.
            csv_delimiter (str): The delimiter for CSV documents.
            escape_html (bool): Whether to escape HTML characters in the comment.
        """
        comment = "" if comment is None else comment
        comment = html.escape(comment, quote=True) if escape_html else comment
        attachment = self._get_attachment(body, source, mime, csv_delimiter)

        # Add extras to Allure report if allure-pytest plugin is being used.
        if self._allure and importlib.util.find_spec('allure') is not None:
            import allure
            if attachment is not None:
                try:
                    if attachment.body is not None:
                        allure.attach(attachment.body, name=comment, attachment_type=attachment.mime)
                    elif attachment.source is not None:
                        allure.attach.file(attachment.source)
                except Exception as err:
                    allure.attach(str(err), name="Error creating Allure attachment", attachment_type=allure.attachment_type.TEXT)

        # Add extras to pytest-html report if pytest-html plugin is being used.
        if self._html:
            if attachment is not None:
                if attachment.body is None and attachment.mime is None and attachment.source is not None:
                    comment += ' ' + attachment.inner_html
                else:
                    comment += '\n' + utils.decorate_attachment(attachment)
            self._save_screenshot(None, None)
            self.comments.append(comment)

    # Deprecated method
    def step(
            self,
            comment: str = None,
            target=None,
            code_block: CodeBlockText = None,
            full_page: bool = True,
            page_source: bool = False,
            escape_html: bool = False
    ):
        """
        Adds a step in the pytest-html report: screenshot, comment and webpage source.
        The screenshot is saved in <report_html>/screenshots folder.
        The webpage source is saved in <report_html>/sources folder.

        Args:
            comment (str): The comment of the test step.
            target (WebDriver | WebElement | Page | Locator): The target of the screenshot.
            code_block (CodeBlockText): The code-block formatted content to be added.
            full_page (bool): Whether to take a full-page screenshot.
            page_source (bool): Whether to include the page source. Overrides the global `sources` fixture.
            escape_html (bool): Whether to escape HTML characters in the comment.
        """
        if target is not None:
            if importlib.util.find_spec('selenium') is not None:
                from selenium.webdriver.remote.webdriver import WebDriver
                if isinstance(target, WebDriver) and self.target is None:
                    self.target = target

            if importlib.util.find_spec('playwright') is not None:
                from playwright.sync_api import Page
                if isinstance(target, Page) and self.target is None:
                    self.target = target

        if self._fx_screenshots == "last" and target is not None:
            return

        # Get the 3 parts of the test step: image, comment and source
        image, source = utils.get_screenshot(target, full_page, self._fx_sources or page_source)
        comment = "" if comment is None else comment
        comment = html.escape(comment, quote=True) if escape_html else comment

        # Add extras to Allure report if allure-pytest plugin is being used.
        if self._allure and importlib.util.find_spec('allure') is not None:
            import allure
            if image is not None:
                allure.attach(image, name=comment, attachment_type=allure.attachment_type.PNG)
                # Attach the webpage source
                if source is not None:
                    allure.attach(source, name="page source", attachment_type=allure.attachment_type.TEXT)
            if code_block is not None and code_block.body is not None:
                allure.attach(code_block.body, name=comment, attachment_type=code_block.mime)

        # Add extras to pytest-html report if pytest-html plugin is being used.
        if self._html:
            self._save_screenshot(image, source)
            if code_block is not None and code_block.body is not None:
                comment += '\n' + utils.decorate_attachment(code_block)
            self.comments.append(comment)

        # Deprecation warning
        warnings.warn(deprecation_msg, DeprecationWarning)

    def _save_screenshot(self, image: bytes | str, source: str):
        """
        Saves the pytest-html 'extras': screenshot, comment and webpage source.
        The screenshot is saved in <report_html>/screenshots folder.
        The webpage source is saved in <report_html>/sources folder.

        Args:
            image (bytes | str): The screenshot as bytes or base64 string.
            source (str): The webpage source code.
        """
        if isinstance(image, str):
            try:
                image = base64.b64decode(image.encode())
            except:
                image = None
        index = -1 if image is None else counter()
        link_image = utils.get_image_link(self._html, index, image)
        self.images.append(link_image)
        link_source = None
        if source is not None:
            link_source = utils.get_source_link(self._html, index, source)
        self.sources.append(link_source)

    def _get_attachment(
        self,
        body: str | Dict | List[str] = None,
        source: str = None,
        mime: str = None,
        delimiter=',',
    ) -> Attachment:
        """
        Creates an attachment.

        Args:
            body (str | Dict | List[str]): The content/body of the attachment.
                Can be of type 'Dict' for JSON mime type.
                Can be of type 'List[str]' for uri-list mime type.
            source (str): The filepath of the source to attach.
            mime (str): The attachment mime type.
            delimiter (str): The delimiter for CSV documents.
        
        Returns:
            An attachment object.
        """
        if source is not None:
            try:
                if mime is None:
                    inner_html = None
                    if self._html:
                        inner_html = utils.decorate_uri(self.add_to_downloads(source))
                    return Attachment(source=source, inner_html=inner_html)
                else:
                    f = open(source, 'r')
                    body = f.read()
                    f.close()
            except Exception as err:
                body = f"Error reading file: {source}\n{err}"
                mime = Mime.text_plain
        if mime == Mime.text_html:
            try:
                encoded_bytes = base64.b64encode(body.encode('utf-8'))
                encoded_str = encoded_bytes.decode('utf-8')
                inner_html = f"data:text/html;base64,{encoded_str}"
                return Attachment(body=body, source=source, mime=mime, inner_html=inner_html)
            except Exception as err:
                body = f"Error encoding HTML body\n{err}"
                mime = Mime.text_plain
        return Attachment.parse_body(body, mime, self._indent, delimiter)

    def link(self, uri: str, name: str = None):
        """
        Adds a link to the report.

        Args:
            uri (str): The link uri.
            name (str): The link text.
        """
        self.links.append((uri, name))

    def add_to_downloads(self, filepath: str = None) -> str:
        """
        When using pytest-html, copies a file into the report's download folder, make it available to download.

        Args:
            filepath (str): The file to add to download folder.

        Returns:
            The uri of the downloadable file.
        """
        if self._html:
            return utils.get_download_link(self._html, filepath)
        else:
            return None

    # Deprecated code from here downwards
    def format_code_block(self, text: str, mime="text/plain") -> Attachment:
        return Attachment(text, mime)
    
    def format_json_file(self, filepath: str, indent=4) -> Attachment:
        """
        Formats the contents of a JSON file.
        """
        try:
            f = open(filepath, 'r')
            content = f.read()
            f.close()
        except:
            content = None
        return self.format_json_str(content, indent)

    def format_json_str(self, text: str, indent: int = 4) -> Attachment:
        """
        Formats a string holding a JSON document.
        """
        return Attachment.parse_body(text, Mime.application_json, indent)

    def format_xml_file(self, filepath: str, indent: int = 4) -> Attachment:
        """
        Formats the contents of an XML file.
        """
        try:
            f = open(filepath, 'r')
            content = f.read()
            f.close()
        except Exception as err:
            content = str(err)
        return self.format_xml_str(content, indent)

    def format_xml_str(self, text: str, indent: int = 4) -> Attachment:
        """
        Formats a string holding an XML document.
        """
        return Attachment.parse_body(text, Mime.application_xml, indent)

    def format_yaml_file(self, filepath: str, indent: int = 4) -> Attachment:
        """
        Formats the contents of a YAML file.
        """
        try:
            f = open(filepath, 'r')
            content = f.read()
            f.close()
        except Exception as err:
            content = str(err)
        return self.format_yaml_str(content, indent)

    def format_yaml_str(self, text: str, indent: int = 4) -> Attachment:
        """
        Formats a string containing a YAML document.
        """
        return Attachment.parse_body(text, Mime.application_yaml, indent)
