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
                 sources: bool, indent: int, report_allure: str):
        """
        Args:
            report_html (str): The HTML report folder.
            single_page (bool): Whether to generate the HTML report in a single webpage.
            screenshots (str): The screenshot strategy. Possible values: 'all' or 'last'.
            sources (bool): Whether to gather webpage sources.
            indent (int): The indent to use to format XML, JSON and YAML documents.
            report_allure (str): The Allure report folder.
        """
        self.images = []
        self.sources = []
        self.comments = []
        self.attachments = []
        self.links = []  # deprecated
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
        image, source = self._get_image_source(target, full_page, page_source)
        self._add_extra(comment, image, source, None, Mime.image_png, escape_html)

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
            source (str): The filepath of the source of the attachment.
            mime (str): The mime type of the attachment.
            csv_delimiter (str): The delimiter for CSV documents.
            escape_html (bool): Whether to escape HTML characters in the comment.
        """
        if Mime.is_unsupported(mime):
            mime = None
        attachment = self._get_attachment(body, source, mime, csv_delimiter)
        mime = attachment.mime if attachment is not None else None
        if Mime.is_image(mime):  # Add image attachments as 'screenshot' step
            self._add_extra(comment, attachment.body, None, None, mime, escape_html)
        else:
            self._add_extra(comment, None, None, attachment, mime, escape_html)

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
            source (str): The filepath of the source of the attachment.
            mime (str): The mime type of the attachment.
            delimiter (str): The delimiter for CSV documents.

        Returns:
            An attachment instance.
        """
        inner_html = None
        if source is not None:
            try:
                if mime is None:
                    if self._html:
                        inner_html = decorators.decorate_uri(self._add_to_downloads(source))
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
        if Mime.is_not_image(mime) and isinstance(body, bytes):  # Attachment of body with unknown mime
            if self._html:
                inner_html = decorators.decorate_uri(self._add_to_downloads(body))
            return Attachment(body=body, inner_html=inner_html)
            # f = self._add_to_downloads(body)
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

    def _get_image_source(
        self,
        target=None,
        full_page: bool = True,
        page_source: bool = False
    ) -> tuple[Optional[bytes], Optional[str]]:
        """
        Gets the screenshot as bytes and the webpage source if applicable.

        Args:
            target (WebDriver | WebElement | Page | Locator): The target of the screenshot.
            full_page (bool): Whether to take a full-page screenshot.
            page_source (bool): Whether to include the page source. Overrides the global `sources` fixture.

        Returns: The screenshot as bytes and the webpage source if applicable.
        """
        self.target = target
        if target is None or self._fx_screenshots == "last":
            return None, None
        return utils.get_screenshot(target, full_page, self._fx_sources or page_source)

    def _save_image_source(self, image: Optional[bytes | str], source: Optional[str], mime: str = "image/*"):
        """
        When not using the --self-contained-html option, saves the image and webpage source
           and returns the filepaths relative to the <report_html> folder.
        The image is saved in <report_html>/images folder.
        The webpage source is saved in <report_html>/sources folder.
        When using the --self-contained-html option, returns the data URI schema of the image and the source.

        Args:
            image (bytes | str): The image as bytes or base64 string.
            source (str): The webpage source.
            mime (str): The mime type of the image.

        Returns:
            The uris of the image and webpage source.
        """
        link_image = None
        link_source = None

        if isinstance(image, str):
            try:
                image = base64.b64decode(image.encode())
            except Exception as error:
                utils.log_error(None, "Error decoding image string:", error)
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
                    utils.log_error(None, "Error encoding image string:", error)
                    data_uri = None
                link_image = data_uri
        # Get the webpage source uri
        if source is not None:
            if self._fx_single_page is False:
                link_source = utils.save_source_and_get_link(self._html, index, source)
            else:
                link_source = f"data:text/plain;base64,{base64.b64encode(source.encode()).decode()}"

        return link_image, link_source

    def _add_extra(
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
            image (bytes | str): The image as bytes or base64 string.
            source (str): The webpage source code.
            attachment (Attachment): The attachment.
            mime (str): The mime type of the attachment.
            escape_html (bool): Whether to escape HTML characters in the comment.
        """
        comment = utils.escape_html(comment) if escape_html else comment

        # Add extras to Allure report if allure-pytest plugin is being used.
        if self._allure and importlib.util.find_spec('allure') is not None:
            import allure
            if image is not None:
                allure.attach(image, name=comment, attachment_type=mime)
                if source is not None:
                    allure.attach(source, name="page source", attachment_type=allure.attachment_type.TEXT)

            elif attachment is not None:
                try:
                    if attachment.body is not None:
                        allure.attach(attachment.body, name=comment, attachment_type=mime)
                    elif attachment.source is not None:
                        allure.attach.file(attachment.source, name=comment)
                except Exception as err:
                    allure.attach(str(err), name="Error adding attachment", attachment_type=allure.attachment_type.TEXT)
            elif comment is not None:
                allure.attach('', name=comment, attachment_type=allure.attachment_type.TEXT)

        # Add extras to pytest-html report if pytest-html plugin is being used.
        if self._html:
            if comment is None and image is None and attachment is None:
                utils.log_error(None, "Empty test step will be ignored.", None)
                return
            link_image, link_source = self._save_image_source(image, source, mime)
            self.images.append(link_image)
            self.sources.append(link_source)
            self.comments.append(comment)
            self.attachments.append(attachment)

    def _add_to_downloads(self, target: str | bytes = None) -> str:
        """
        When using pytest-html, copies a file into the report's download folder, making it available to download.

        Args:
            target (str | bytes): The file or the bytes content to add into the download folder.

        Returns:
            The uri of the downloadable file.
        """
        return utils.save_file_and_get_link(self._html, target)

    # DEPRECATED CODE
    def link(self, uri: str, name: str = None):
        """
        Adds a link to the report.

        Args:
            uri (str): The link uri.
            name (str): The link text.
        """
        # Deprecation warning
        import warnings
        warnings.warn(deprecation_msg, DeprecationWarning)
        self.links.append((uri, name))


deprecation_msg = """
        
report.link method is deprecated and will be removed in the next major version release
        
Please use pytest.mark.link decorator:
    @pytest.mark.link("<url>")
    @pytest.mark.link("<url>", "<name>")
    @pytest.mark.link(url="<url>", name="<name>")
"""
