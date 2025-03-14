import base64
import importlib
from typing import Literal
from typing import Optional
from . import decorators
from . import utils
from .attachment import Attachment
from .mime import Mime


class Extras:
    """
    Class to hold pytest-html 'extras' to be added for each test in the HTML report.
    """

    def __init__(self, report_html: str, single_page: bool, screenshots: Literal["all", "last", "fail", "none"],
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
        self.comments = []
        self.multimedia = []
        self.sources = []
        self.attachments = []
        self.target = None
        self._fx_screenshots = screenshots
        self._fx_sources = sources
        self._fx_single_page = single_page
        self._fx_html = report_html
        self._fx_allure = report_allure
        self._fx_indent = indent
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
        Adds a step with a screenshot to the report.

        Args:
            comment (str): The comment of the test step.
            target (WebDriver | WebElement | Page | Locator): The target of the screenshot.
            full_page (bool): Whether to take a full-page screenshot.
            page_source (bool): Whether to include the page source. Overrides the global `sources` fixture.
            escape_html (bool): Whether to escape HTML characters in the comment.
        """
        target_valid, target_obj = utils.check_screenshot_target_type(target)
        self.target = target_obj if self.target is None else self.target
        if self._fx_screenshots != "all":
            return
        if target is not None and not target_valid:
            utils.log_error(None, "The screenshot target is not an instance of WebDriver, WebElement, Page or Locator")
            return
        try:
            image, source = self._get_image_source(target, full_page, page_source)
        except Exception:
            self.comments.append(comment)
            self.multimedia.append(utils.error_screenshot)
            self.sources.append(None)
            self.attachments.append(None)
            return
        if target is None:  # A comment alone
            self._add_extra(comment, None, None, escape_html)
        else:
            self._add_extra(comment, source, Attachment(image, None, Mime.PNG, None), escape_html)

    def attach(
        self,
        comment: str,
        body: str | bytes | dict | list[str] = None,
        source: str = None,
        mime: str = None,
        csv_delimiter: str = ',',
        escape_html: bool = False
    ):
        """
        Adds a step with an attachment to the report.
        The 'body' and 'source' parameters are exclusive.

        Args:
            comment (str): The comment of the test step.
            body (str | bytes | dict | list[str]): The content/body of the attachment or the bytes of the screenshot.
                Can be of type 'dict' for JSON mime type.
                Can be of type 'list[str]' for uri-list mime type.
                Can be of type 'bytes' for image mime type.
            source (str): The filepath of the source of the attachment.
            mime (str): The mime type of the attachment.
            csv_delimiter (str): The delimiter for CSV documents.
            escape_html (bool): Whether to escape HTML characters in the comment.
        """
        if body is None and source is None:
            if comment is not None:  # A comment alone
                attachment = Attachment(body="", mime=Mime.TEXT)
            else:
                attachment = None
        else:
            if body is not None and mime is None:
                attachment = Attachment(body="Mime is required for attachments with body", mime=Mime.TEXT)
            else:
                mime = Mime.get_mime(mime)
                attachment = self._get_attachment(body, source, mime, csv_delimiter)
        self._add_extra(comment, None, attachment, escape_html)

    def _get_attachment(
        self,
        body: str | dict | list[str] | bytes = None,
        source: str = None,
        mime: Mime = None,
        delimiter=',',
    ) -> Attachment:
        """
        Creates an attachment from its body or source.

        Args:
            body (str | bytes | dict | list[str]): The content/body of the attachment or the bytes of the screenshot.
                Can be of type 'dict' for JSON mime type.
                Can be of type 'list[str]' for uri-list mime type.
                Can be of type 'bytes' for image mime type.
            source (str): The filepath of the source of the attachment.
            mime (Mime): The mime type of the attachment.
            delimiter (str): The delimiter for CSV documents.

        Returns:
            An attachment instance.
        """
        inner_html = None
        if source is not None:
            try:
                if Mime.is_unsupported(mime):
                    if self._fx_html:
                        inner_html = decorators.decorate_uri(
                            utils.copy_file_and_get_link(self._fx_html, source, Mime.get_extension(mime), "downloads")
                        )
                    if inner_html == '':
                        return Attachment(body="Error copying file", mime=Mime.TEXT)
                    else:
                        # mime = None to avoid displaying attachment in <pre> tag
                        return Attachment(source=source, inner_html=inner_html)
                if mime is not None:
                    if Mime.is_multimedia(mime) and mime != Mime.SVG:
                        return Attachment(source=source, mime=mime)
                    else:
                        f = open(source, 'r')
                        body = f.read()
                        f.close()
            except Exception as error:
                body = f"Error creating attachment from source {source}\n{error}"
                utils.log_error(None, f"Error creating attachment from source {source}: ", error)
                mime = Mime.TEXT

        else:
            # Continue processing attachments with body
            if Mime.is_unsupported(mime):  # Attachment of body with unknown mime
                if self._fx_html:
                    inner_html = decorators.decorate_uri(
                        utils.save_data_and_get_link(self._fx_html, body, Mime.get_extension(mime), "downloads")
                    )
                # mime = None to avoid displaying attachment in <pre> tag
                return Attachment(body=body, inner_html=inner_html)
                # f = utils.save_data_and_get_link(self._fx_html, body, Mime.get_extension(mime))
                # body = [f]
                # mime = Mime.URI
        if mime == Mime.HTML:
            try:
                encoded_bytes = base64.b64encode(body.encode("utf-8"))
                encoded_str = encoded_bytes.decode("utf-8")
                inner_html = f"data:text/html;base64,{encoded_str}"
                return Attachment(body=body, mime=mime, inner_html=inner_html)
            except Exception as error:
                body = f"Error encoding HTML body\n{error}"
                utils.log_error(None, "Error encoding HTML body", error)
                mime = Mime.TEXT
        if mime == Mime.SVG:
            return Attachment(body=body, source=source, mime=mime)
        return Attachment.parse_body(body, mime, self._fx_indent, delimiter)

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

    def _save_image_video_source(self, data: Optional[bytes | str], source: Optional[str], mime: Optional[Mime]):
        """
        When not using the --self-contained-html option, saves the image or video and webpage source, if applicable,
           and returns the filepaths relative to the <report_html> folder.
        The image is saved in <report_html>/images folder.
        The video is saved in <report_html>/videos folder.
        The webpage source is saved in <report_html>/sources folder.
        When using the --self-contained-html option, returns the data URI schema of the image and the source.

        Args:
            data (bytes | str): The image/video as bytes or base64 string.
            source (str): The webpage source.
            mime (Mime): The mime type of the image/video.

        Returns:
            The uris of the image/video and webpage source.
        """
        if data is None:
            return None, None
        if mime is None or Mime.is_not_multimedia(mime):
            utils.log_error(None, "Invalid mime type '{mime}' for multimedia content:")
            return None, None

        link_multimedia = None
        link_source = None
        data_str = None
        data_b64 = None
        extension = Mime.get_extension(mime)

        if isinstance(data, str):
            if mime == Mime.SVG:
                data_str = data
                data_b64 = data
            else:
                try:
                    data_str = data
                    data_b64 = base64.b64decode(data.encode())
                except Exception as error:
                    utils.log_error(None, "Error decoding image/video base64 string:", error)
                    return None, None
        else:
            try:
                data_b64 = data
                data_str = base64.b64encode(data).decode()
            except Exception as error:
                utils.log_error(None, "Error encoding image/video bytes:", error)
                return None, None

        if Mime.is_video(mime):
            if self._fx_single_page is False:
                link_multimedia = utils.save_data_and_get_link(self._fx_html, data_b64, extension, "videos")
            else:
                link_multimedia = f"data:{mime};base64,{data_str}"
            return link_multimedia, None

        if Mime.is_image(mime):
            if self._fx_single_page is False:
                link_multimedia = utils.save_data_and_get_link(self._fx_html, data_b64, extension, "images")
            else:
                link_multimedia = f"data:{mime};base64,{data_str}"

        if source is not None:
            if self._fx_single_page is False:
                link_source = utils.save_data_and_get_link(self._fx_html, source, None, "sources")
            else:
                link_source = f"data:text/plain;base64,{base64.b64encode(source.encode()).decode()}"

        return link_multimedia, link_source

    def _copy_image_video(self, filepath: str, mime: Optional[Mime]) -> Optional[str]:
        """
        Copies the image or video and returns the filepath relative to the <report_html> folder.
        The image is copied into <report_html>/images folder.
        The video is copied into <report_html>/videos folder.
        When using the --self-contained-html option, returns the data URI schema of the image/video.

        Args:
            filepath (str): The filepath of the image/video to copy.
            mime (Mime): The mime type of the image/video.

        Returns:
            The uris of the image/video and webpage source.
        """
        if mime is None or Mime.is_not_multimedia(mime):
            utils.log_error(None, f"invalid mime type '{mime}' for multimedia file '{filepath}")
            return None

        data_str = ""
        extension = Mime.get_extension(mime)
        if self._fx_single_page:
            try:
                f = open(filepath, "rb")
                data_b64 = f.read()
                f.close()
                data_str = base64.b64encode(data_b64).decode()
            except Exception as error:
                utils.log_error(None, f"Error reading image/video file '{filepath}'", error)
                return None
            return f"data:{mime};base64,{data_str}"

        if Mime.is_video(mime):
            return utils.copy_file_and_get_link(self._fx_html, filepath, extension, "videos")

        if Mime.is_image(mime):
            return utils.copy_file_and_get_link(self._fx_html, filepath, extension, "images")

    def _add_extra(
        self,
        comment: str,
        websource: Optional[str],
        attachment: Optional[Attachment],
        escape_html: bool
    ):
        """
        Adds the comment, webpage source and attachment to the lists of the 'report' fixture.
        Screenshots are stored in the attachment argument.
        Images are saved in <report_html>/images folder.
        Webpage sources are saved in <report_html>/sources folder.
        Videos are saved in <report_html>/videos folder.
        Other types of files are saved in <report_html>/downloads folder.

        Args:
            comment (str): The comment of the test step.
            websource (str): The webpage source code.
            attachment (Attachment): The attachment.
            escape_html (bool): Whether to escape HTML characters in the comment.
        """
        comment = utils.escape_html(comment) if escape_html else comment
        link_multimedia = None
        link_source = None
        mime = attachment.mime if attachment is not None else None

        # Add extras to Allure report if allure-pytest plugin is being used.
        if self._fx_allure and importlib.util.find_spec("allure") is not None:
            import allure
            if attachment is not None:
                try:
                    if attachment.body is not None:
                        allure.attach(attachment.body, name=comment, attachment_type=mime)
                    elif attachment.source is not None:
                        allure.attach.file(attachment.source, name=comment)
                    if websource is not None:
                        allure.attach(websource, name="page source", attachment_type=allure.attachment_type.TEXT)
                except Exception as err:
                    allure.attach(str(err), name="Error adding attachment", attachment_type=allure.attachment_type.TEXT)
            else:  # Comment alone
                allure.attach("", name=comment, attachment_type=allure.attachment_type.TEXT)

        # Add extras to pytest-html report if pytest-html plugin is being used.
        if self._fx_html:
            if comment is None and attachment is None:
                utils.log_error(None, "Empty test step will be ignored.", None)
                return
            if attachment is not None and Mime.is_multimedia(mime):
                msg = None
                if attachment.source is not None:
                    link_multimedia, link_source = self._copy_image_video(attachment.source, mime), None
                    msg = "Error copying file" if link_multimedia is None else None
                else:
                    link_multimedia, link_source = self._save_image_video_source(attachment.body, websource, mime)
                    msg = "Error saving data" if link_multimedia is None else None
                if msg is not None:
                    attachment = Attachment(body=msg, mime=Mime.TEXT)
                else:  # Cleanup of useless attachment's info
                    if Mime.is_video(mime):
                        attachment.body = None
                    if Mime.is_image_binary(mime):
                        attachment = None
            self.comments.append(comment)
            self.multimedia.append(link_multimedia)
            self.sources.append(link_source)
            self.attachments.append(attachment)
