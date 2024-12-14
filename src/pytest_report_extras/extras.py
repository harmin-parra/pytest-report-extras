import base64
import html
import importlib
import json
import re
import xml.parsers.expat as expat
import xml.dom.minidom as xdom
import yaml
from . import utils


# Counter used for image and page source files naming
count = 0


def counter() -> int:
    """ Returns a suffix used for image and webpage source file naming """
    global count
    count += 1
    return count


class Extras:
    """
    Class to hold pytest-html 'extras' to be added for each test in the HTML report.
    """

    def __init__(self, report_folder, fx_screenshots, fx_sources, report_allure):
        """
        Args:
            report_folder (str): The 'report_folder' fixture.
            fx_screenshots (str): The 'screenshots' fixture.
            fx_sources (bool): The 'sources' fixture.
            report_allure (str): The 'report_allure' fixture.
        """
        self.images = []
        self.sources = []
        self.comments = []
        self.target = None
        self.attachment_type = None
        self._fx_screenshots = fx_screenshots
        self._fx_sources = fx_sources
        self._folder = report_folder
        self._allure = report_allure

    def step(self, comment: str = None, target=None, code_block: str = None, full_page: bool = True, escape_html: bool = False):
        """
        Adds a step in the pytest-html report: screenshot, comment and webpage source.
        The screenshot is saved in <forder_report>/screenshots folder.
        The webpage source is saved in <forder_report>/sources folder.

        Args:
            comment (str): The comment of the test step.
            target (WebDriver | WebElement | Page | Locator): The target of the screenshot.
            code_block (str): The code-block formatted text to be added.
            full_page (bool): Whether to take a full-page screenshot.
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
        image, source = utils.get_screenshot(target, full_page, self._fx_sources)
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
            if code_block is not None:
                if self.attachment_type is None:
                    self.attachment_type = "text/plain"
                allure.attach(code_block, name=comment, attachment_type=self.attachment_type)

        self.attachment_type = None

        # Add extras to pytest-html report
        self._save_screenshot(image, source)
        if code_block is not None:
            comment += '\n' + code_block
        self.comments.append(comment)


    def _save_screenshot(self, image: bytes | str, source: str):
        """
        Saves the pytest-html 'extras': screenshot, comment and webpage source.
        The screenshot is saved in <forder_report>/screenshots folder.
        The webpage source is saved in <forder_report>/sources folder.

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
        link_image = utils.get_image_link(self._folder, index, image)
        self.images.append(link_image)
        link_source = None
        if source is not None:
            link_source = utils.get_source_link(self._folder, index, source)
        self.sources.append(link_source)

    def format_code_block(self, content) -> str:
        if content is None:
            self.attachment_type = None
            return None
        self.attachment_type = "text/plain"
        # content = content.replace('<', '&lt;').replace('>', '&gt;')
        content = utils.escape_html(content)
        return f'<pre class="extras_pre">{content}</pre>'

    def format_json_file(self, filepath, indent=4) -> str:
        """
        Formats the contents of a JSON file.
        """
        f = open(filepath, 'r')
        content = f.read()
        f.close()
        return self.format_json_str(content, indent)

    def format_json_str(self, content, indent=4) -> str:
        """
        Formats a string holding a JSON content.
        """
        self.attachment_type = "application/json"
        content = json.loads(content)
        return self.format_code_block(json.dumps(content, indent=indent))

    def format_xml_file(self, filepath, indent=4) -> str:
        """
        Formats the contents of a XML file.
        """
        f = open(filepath, 'r')
        content = f.read()
        f.close()
        return self.format_xml_str(content, indent)

    def format_xml_str(self, content, indent=4) -> str:
        """
        Formats a string holding a XML content.
        """
        self.attachment_type = "application/xml"
        result = None
        try:
            result = xdom.parseString(re.sub(r"\n\s+", '',  content).replace('\n','')).toprettyxml(indent=" " * indent)
        except expat.ExpatError:
            if content is None:
                content = 'None'
            result = "Raw text:\n" + content
        return self.format_code_block(result)

    def format_yaml_file(self, filepath, indent=4) -> str:
        """
        Formats the contents of a YAML file.
        """
        f = open(filepath, 'r')
        content = f.read()
        f.close()
        return self.format_yaml_str(content, indent)

    def format_yaml_str(self, content, indent=4) -> str:
        """
        Formats a string containing a YAML document content.
        """
        self.attachment_type = "application/yaml"
        content = yaml.safe_load(content)
        return self.format_code_block(yaml.dump(content, indent=indent))
