import base64
import html
import importlib
from . import utils
from .attachment import Attachment
from .attachment import Mime
import warnings


deprecation_msg = """

report.step(comment: str, code_block: CodeBlockText) is deprecated and will be removed in the next major version release

Please use: report.step(comment: str', attachment: Attachment)

Examples:
report.step(
    comment="comment",
    attachment=report.attachment(text="<XML string>", mime=report.Mime.application_xml)
)
report.step(
    comment="comment",
    attachment=report.attachment(file="/path/to/JSON file", mime=report.Mime.application_json)
)"""


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

    def step(
            self,
            comment: str = None,
            target=None,
            attachment: Attachment = None,
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
            attachment (Attachment): The attachment to be added.
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
            if attachment is not None and attachment.text is not None:
                allure.attach(attachment.text, name=comment, attachment_type=attachment.mime)
            # Deprecated attachment
            if code_block is not None and code_block.text is not None:
                allure.attach(code_block.text, name=comment, attachment_type=code_block.mime)

        # Add extras to pytest-html report if pytest-html plugin is being used.
        if self._html:
            self._save_screenshot(image, source)
            if attachment is not None and attachment.text is not None:
                comment += '\n' + attachment.get_html_tag()
            # Deprecated attachment
            if code_block is not None and code_block.text is not None:
                comment += '\n' + code_block.get_html_tag()
            self.comments.append(comment)

        # Deprecation warning
        if code_block is not None:
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

    def attachment(self, text: str = None, file: str = None, mime: str = Mime.text_plain) -> Attachment:
        """
        Creates an attachment for a step.
        Args:
            text (str): The content of the attachment.
            file (str): The filepath of the file to attach.
            mime (str): The attachment mime type (Necessary for Allure report).
        """
        if file is not None:
            try:
                f = open(file, 'r')
                text = f.read()
                f.close()
            except Exception as err:
                text = str(err)
                mime = Mime.text_plain
        return Attachment.parse_text(text, mime, self._indent)

    def link(self, uri: str, name: str = None):
        """
        Adds a link to the report.
        Args:
            uri (str): The link URI
            name (str): The link text
        """
        self.links.append((uri, name))

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
        return Attachment.parse_text(text, Mime.application_json, indent)

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
        return Attachment.parse_text(text, Mime.application_xml, indent)

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
        return Attachment.parse_text(text, Mime.application_yaml, indent)
