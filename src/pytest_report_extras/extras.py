import base64
import importlib
from typing import Literal
from typing import Optional
from . import decorators
from . import utils
from .attachment import Attachment
from .attachment import Mime


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
    def __init__(self, report_html: str, single_page: bool, screenshots: Literal["all", "last"],
                 sources: bool, report_allure: str, indent: int):
        """
        Args:
            report_html (str): The HTML report folder.
            single_page (bool): Whether to generate the HTML report in a single webpage.
            screenshots (str): The screenshot strategy. Possible values: 'all' or 'last'.
            sources (bool): Whether to gather webpage sources.
            report_allure (str): The Allure report folder.
            indent (int): The indent to use to format XML, JSON and YAML documents.
        """
        self.images = []
        self.sources = []
        self.comments = []
        self.attachments = []
        self.links = []
        self.target = None
        self._fx_screenshots = screenshots
        self._fx_sources = sources
        self._fx_single_page = single_page
        self._html = report_html
        self._allure = report_allure
        self._indent = indent
        self.Mime = Mime

    def screenshot(
        self,
        comment: str,
        target=None,
        full_page: bool = True,
        page_source: bool = False,
        escape_html: bool = False
    ):
        """
        Adds a step with a screenshot in the report.
        The screenshot is saved in <report_html>/images folder.
        The webpage source is saved in <report_html>/sources folder.

        Args:
            comment (str): The comment of the test step.
            target (WebDriver | WebElement | Page | Locator): The target of the screenshot.
            full_page (bool): Whether to take a full-page screenshot.
            page_source (bool): Whether to include the page source. Overrides the global `sources` fixture.
            escape_html (bool): Whether to escape HTML characters in the comment.
        """
        self._add_image_step(
            comment=comment,
            target=target,
            full_page=full_page,
            page_source=page_source,
            data=None,
            mime=None,
            escape_html=escape_html
        )

    def attach(
        self,
        comment: str,
        body: str | bytes | dict | list[str] = None,
        source: str = None,
        mime: str = None,
        csv_delimiter=',',
        escape_html: bool = False
    ):
        """
        Adds a step with an attachment to the report.
        The image is saved in <report_html>/images folder.
        The webpage source is saved in <report_html>/sources folder.
        The 'body' and 'source' parameters are exclusive.

        Args:
            comment (str): The comment of the test step.
            body (str | bytes | dict | list[str]): The content/body of the attachment.
                Can be of type 'dict' for JSON mime type.
                Can be of type 'list[str]' for uri-list mime type.
                Can be of type 'bytes' for image mime type.
            source (str): The filepath of the source to attach.
            mime (str): The attachment mime type.
            csv_delimiter (str): The delimiter for CSV documents.
            escape_html (bool): Whether to escape HTML characters in the comment.
        """
        if Mime.is_unsupported(mime):
            mime = None
        attachment = self._get_attachment(body, source, mime, csv_delimiter)
        mime = attachment.mime
        if Mime.is_image(mime):  # Treat attachment of images like screenshots
            self._add_image_step(comment=comment, data=attachment.body, mime=mime, escape_html=escape_html)
        else:
            self._add_extras(comment, None, None, attachment, mime, escape_html)

    def _add_image_step(
        self,
        comment: str,
        target=None,
        full_page: bool = True,
        page_source: bool = False,
        data: bytes = None,
        mime: Mime = None,
        escape_html: bool = False
    ):
        """
        Adds a step with an image in the report.
        The image/screenshot is saved in <report_html>/images folder.
        The webpage source is saved in <report_html>/sources folder.
        The 'target' and 'data' parameters are exclusive.

        Args:
            comment (str): The comment of the test step.
            target (WebDriver | WebElement | Page | Locator): The target of the screenshot.
            full_page (bool): Whether to take a full-page screenshot.
            page_source (bool): Whether to include the page source. Overrides the global `sources` fixture.
            data (bytes): The image to attach as bytes.
            mime (str): The mime type of the image.
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

        if self._fx_screenshots == "last" and target is not None and data is None:
            return

        # Get the 3 parts of the test step: image, comment and source
        if target is not None:
            image, source = utils.get_screenshot(target, full_page, self._fx_sources or page_source)
            mime = "image/png"
        else:  # data is not None
            image, source = data, None
            mime = "image/*" if mime is None else mime

        self._add_extras(comment, image, source, None, mime, escape_html)

    def _get_attachment(
        self,
        body: str | dict | list[str] | bytes = None,
        source: str = None,
        mime: str = None,
        delimiter=',',
    ) -> Attachment:
        """
        Creates an attachment.

        Args:
            body (str | bytes | dict | list[str]): The content/body of the attachment.
                Can be of type 'dict' for JSON mime type.
                Can be of type 'list[str]' for uri-list mime type.
                Can be of type 'bytes' for image mime type.
            source (str): The filepath of the source to attach.
            mime (str): The attachment mime type.
            delimiter (str): The delimiter for CSV documents.

        Returns:
            An attachment instance.
        """
        inner_html = None
        if source is not None:
            try:
                if mime is None:
                    if self._html:
                        inner_html = decorators.decorate_uri(self.add_to_downloads(source))
                    return Attachment(source=source, inner_html=inner_html)
                else:
                    if Mime.is_image(mime):
                        f = open(source, "rb")
                        body = f.read()
                        f.close()
                    else:
                        f = open(source, 'r')
                        body = f.read()
                        f.close()
            except Exception as error:
                body = f"Error reading file: {source}\n{error}"
                utils.log_error(None, f"Error reading file: {source}", error)
                mime = Mime.text_plain
        if not Mime.is_image(mime) and isinstance(body, bytes):
            if self._html:
                inner_html = decorators.decorate_uri(self.add_to_downloads(body))
            return Attachment(body=body, inner_html=inner_html)
            # f = self.add_to_downloads(body)
            # body = [f]
            # mime = Mime.text_uri_list
        if mime == Mime.text_html:
            try:
                encoded_bytes = base64.b64encode(body.encode('utf-8'))
                encoded_str = encoded_bytes.decode('utf-8')
                inner_html = f"data:text/html;base64,{encoded_str}"
                return Attachment(body=body, mime=mime, inner_html=inner_html)
            except Exception as error:
                body = f"Error encoding HTML body\n{error}"
                utils.log_error(None, "Error encoding HTML body", error)
                mime = Mime.text_plain
        return Attachment.parse_body(body, mime, self._indent, delimiter)

    def _add_extras(
        self,
        comment: str,
        image: Optional[bytes],
        source: Optional[str],
        attachment: Optional[Attachment],
        mime: Optional[str],
        escape_html: bool
    ):
        """
        Adds the comment, image, webpage source and attachment to the lists of the 'report' fixture.

        Args:
            comment (str): The comment of the test step.
            image (bytes | str): The image as bytes or base64 string..
            source (str):: The webpage HTML source code.
            mime (str): The mime type of the image.
            escape_html (bool): Whether to escape HTML characters in the comment.

        """
        comment = utils.escape_html(comment) if escape_html else comment

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
            self._save_image(image, source, mime)
            self.comments.append(comment)
            self.attachments.append(attachment)

    def _save_image(self, image: Optional[bytes | str], source: Optional[str], mime: str = "image/*"):
        """
        Saves a screenshot and a webpage source when using the --self-contained-html option of pytest-html plugin
        The image is saved in <report_html>/images folder.
        The webpage source is saved in <report_html>/sources folder.

        Otherwise, saves the data URI schema of the image and the webpage source.

        The image and source HTML anchor 'html' attribute are saved in the
          'images' and 'source' lists of the 'report' fixture.

        Args:
            image (bytes | str): The image as bytes or base64 string.
            source (str): The webpage source.
            mime (str): The mime type of the image.
        """
        link_image = None
        link_source = None

        if isinstance(image, str):
            try:
                image = base64.b64decode(image.encode())
            except Exception as error:
                utils.log_error(None, "Error encoding image string:", error)
                image = None
        # suffix for file names
        index = (0 if self._fx_single_page or (image is None and source is None)
                 else counter())
        # Get the image uri
        if image is not None:
            if self._fx_single_page is False:
                link_image = utils.save_image_and_get_link(self._html, index, image)
            else:
                mime = "image/*" if mime is None else mime
                try:
                    data_uri = f"data:{mime};base64,{base64.b64encode(image).decode()}"
                except Exception as error:
                    utils.log_error(None, "Error encoding string:", error)
                    data_uri = None
                link_image = data_uri
        # Get the webpage source uri
        if source is not None:
            if self._fx_single_page is False:
                link_source = utils.save_source_and_get_link(self._html, index, source)
            else:
                link_source = f"data:text/plain;base64,{base64.b64encode(source.encode()).decode()}"
        self.images.append(link_image)
        self.sources.append(link_source)

    def link(self, uri: str, name: str = None):
        """
        Adds a link to the report.

        Args:
            uri (str): The link uri.
            name (str): The link text.
        """
        self.links.append((uri, name))

    def add_to_downloads(self, target: str | bytes = None) -> str:
        """
        When using pytest-html, copies a file into the report's download folder, making it available to download.

        Args:
            target (str | bytes): The file or the bytes content to add into the download folder.

        Returns:
            The uri of the downloadable file.
        """
        return utils.save_file_and_get_link(self._html, target)
