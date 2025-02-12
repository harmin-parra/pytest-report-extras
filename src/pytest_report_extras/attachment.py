import base64
import csv
import io
import json
import re
import xml.dom.minidom as xdom
import yaml
from typing import List
from typing import Optional
# from typing import Self (python 3.11)
from . import decorators
from . import utils


class Mime:
    """
    Class to hold mime type values.
    """
    application_json = "application/json"
    application_xml = "application/xml"
    application_yaml = "application/yaml"
    image_bmp = "image/png"
    image_gif = "image/gif"
    image_jpeg = "image/jpeg"
    image_png = "image/png"
    image_svg_xml = "image/svg+xml"
    image_tiff = "image/tiff"
    text_csv = "text/csv"
    text_html = "text/html"
    text_plain = "text/plain"
    text_uri_list = "text/uri-list"
    video_mp4 = "video/mp4"
    video_ogg = "video/ogg"
    video_ogv = "video/ogv"
    video_webm = "video/webm"

    @staticmethod
    def is_supported(mime: str):
        return mime in (
            Mime.image_bmp, Mime.image_gif, Mime.image_jpeg, Mime.image_png,
            Mime.image_svg_xml, mime == Mime.image_tiff,
            Mime.text_csv, Mime.text_html, Mime.text_plain, Mime.text_uri_list,
            Mime.video_mp4, Mime.video_ogg, Mime.video_ogv, Mime.video_webm,
            Mime.application_json, Mime.application_xml, Mime.application_yaml
        )

    @staticmethod
    def is_application(mime: str):
        return mime is not None and mime.startswith("application/")

    @staticmethod
    def is_image(mime: str):
        return mime is not None and mime.startswith("image/")

    @staticmethod
    def is_image_binary(mime: str):
        """ Whether the mime type represents an image in binary format: png, mpeg, gif, tiff """
        return mime is not None and mime.startswith("image/") and not mime.startswith("image/svg")

    @staticmethod
    def is_video(mime: str):
        return mime is not None and mime.startswith("video/")

    @staticmethod
    def is_multimedia(mime: str):
        return Mime.is_image(mime) or Mime.is_video(mime)

    @staticmethod
    def is_unsupported(mime: str):
        return not Mime.is_supported(mime)

    @staticmethod
    def is_not_image(mime: str):
        return not Mime.is_image(mime)

    @staticmethod
    def is_not_video(mime: str):
        return not Mime.is_video(mime)

    @staticmethod
    def is_not_multimedia(mime: str):
        return not Mime.is_multimedia(mime)


class Attachment:
    """
    Class to represent attachments.
    """
    def __init__(
        self,
        body: Optional[str | dict | list[str] | bytes] = None,
        source: Optional[str] = None,
        mime: Optional[str] = None,
        inner_html: Optional[str] = None
    ):
        """
        Args:
            body (str | dict | list[str] | bytes): The content/body of the body (optional).
                Can be of type 'dict' for JSON mime type.
                Can be of type 'list[str]' for uri-list mime type.
                Can be of type 'bytes' for image mime type.
            source (str): The filepath of the source (optional).
            mime (str): The mime type (optional).
            inner_html: The inner_html to display the attachment in the HTML report.
                        Used for mime types: text/csv, text/html, text/uri-list and also for unsupported mime types.
        """
        self.body = body
        self.source = source
        self.mime = mime
        self.inner_html = inner_html

    @staticmethod
    def parse_body(
        body: str | dict | list[str] | bytes,
        mime: str = Mime.text_plain,
        indent: int = 4,
        delimiter=',',
    ):  # -> Self | None:
        """
        Creates an attachment from the content/body.

        Args:
            body (str | dict | list[str] | bytes): The content/body of the body.
                Can be of type 'dict' for JSON mime type.
                Can be of type 'list[str]' for uri-list mime type.
                Can be of type 'bytes' for image mime type.
            mime (str): The mime type (optional).
            indent: The indent for XML, JSON and YAML attachments.
            delimiter (str): The delimiter for CSV documents.

        Returns:
            An Attachment object representing the attachment.
        """
        if body in (None, ''):
            return Attachment(body="Body or source is None or empty", mime=Mime.text_plain)
        if body is not None and isinstance(body, List):
            mime = Mime.text_uri_list
        if Mime.is_image(mime):
            return _attachment_image(body, mime)
        if Mime.is_video(mime):
            return _attachment_video(body, mime)
        match mime:
            case Mime.application_json:
                return _attachment_json(body, indent)
            case Mime.application_xml:
                return _attachment_xml(body, indent)
            case Mime.application_yaml:
                return _attachment_yaml(body, indent)
            case Mime.text_csv:
                return _attachment_csv(body, delimiter=delimiter)
            case Mime.text_uri_list:
                return _attachment_uri_list(body)
            case _:
                return _attachment_txt(body)

    def __repr__(self) -> str:
        if isinstance(self.body, bytes):
            body_str = base64.b64encode(self.body).decode()
        else:
            body_str = self.body
        body_str = repr(body_str) if len(repr(body_str)) < 50 else repr(body_str)[:50] + "....'"
        inner_str = repr(self.inner_html) if len(repr(self.inner_html)) < 50 else repr(self.inner_html)[:50] + "....'"
        return (
            '{ ' + f"body: {body_str}, "
            f"source: {repr(self.source)}, "
            f"mime: {repr(self.mime)}, "
            f"inner_html: {inner_str}" + ' }'
        )


def _attachment_json(text: str | dict, indent: int = 4) -> Attachment:
    """
    Returns an attachment object with a string holding a JSON document.
    """
    if not isinstance(text, (str, dict)):
        msg = f"Error parsing JSON body of type '{type(text)}'"
        utils.log_error(None, msg)
        return Attachment(body=msg, mime=Mime.text_plain)
    try:
        text = json.loads(text) if isinstance(text, str) else text
        return Attachment(body=json.dumps(text, indent=indent), mime=Mime.application_json)
    except Exception as error:
        utils.log_error(None, "Error formatting JSON:", error)
        return Attachment(body="Error formatting JSON:\n" + str(text), mime=Mime.text_plain)


def _attachment_xml(text: str, indent: int = 4) -> Attachment:
    """
    Returns an attachment object with a string holding an XML document.
    """
    if not isinstance(text, str):
        msg = f"Error parsing XML body of type '{type(text)}'"
        utils.log_error(None, msg)
        return Attachment(body=msg, mime=Mime.text_plain)
    try:
        result = (xdom.parseString(re.sub(r"\n\s+", '',  text).replace('\n', ''))
                  .toprettyxml(indent=" " * indent))
        result = '\n'.join(line for line in result.splitlines() if not re.match(r"^\s*<!--.*?-->\s*\n*$", line))
        return Attachment(body=result, mime=Mime.application_xml)
    except Exception as error:
        utils.log_error(None, "Error formatting XML:", error)
        return Attachment(body="Error formatting XML:\n" + str(text), mime=Mime.text_plain)


def _attachment_yaml(text: str, indent: int = 4) -> Attachment:
    """
    Returns an attachment object with a string holding a YAML document.
    """
    if not isinstance(text, str):
        msg = f"Error parsing YAML body of type '{type(text)}'"
        utils.log_error(None, msg)
        return Attachment(body=msg, mime=Mime.text_plain)
    try:
        text = yaml.safe_load(text)
        return Attachment(body=yaml.dump(text, indent=indent), mime=Mime.application_yaml)
    except Exception as error:
        utils.log_error(None, "Error formatting YAML:", error)
        return Attachment(body="Error formatting YAML:\n" + str(text), mime=Mime.text_plain)


def _attachment_txt(text: str) -> Attachment:
    """
    Returns an attachment object with a plain/text string.
    """
    if not isinstance(text, str):
        msg = f"Error parsing text body of type '{type(text)}'"
        utils.log_error(None, msg, None)
        return Attachment(body=msg, mime=Mime.text_plain)
    return Attachment(body=text, mime=Mime.text_plain)


def _attachment_csv(text: str, delimiter=',') -> Attachment:
    """
    Returns an attachment object with a string holding a CVS document.
    """
    if not isinstance(text, str):
        msg = f"Error parsing csv body of type '{type(text)}'"
        utils.log_error(None, msg)
        return Attachment(body=msg, mime=Mime.text_plain)
    try:
        f = io.StringIO(text)
        csv_reader = csv.reader(f, delimiter=delimiter)
        inner_html = "<table>"
        for row in csv_reader:
            inner_html += "<tr>"
            for cell in row:
                if csv_reader.line_num == 1:
                    inner_html += f"<th>{cell}</th>"
                else:
                    inner_html += f"<td>{cell}</td>"
            inner_html += "</tr>"
        inner_html += "</table>"
        return Attachment(body=text, mime=Mime.text_csv, inner_html=inner_html)
    except Exception as error:
        utils.log_error(None, "Error formatting CSV:", error)
        return Attachment(body="Error formatting CSV:\n" + str(text), mime=Mime.text_plain)


def _attachment_uri_list(text: str | list[str]) -> Attachment:
    """
    Returns an attachment object with a uri list.
    """
    if not isinstance(text, (str, list)):
        msg = f"Error parsing uri-list body of type '{type(text)}'"
        utils.log_error(None, msg)
        return Attachment(body=msg, mime=Mime.text_plain)
    try:
        uri_list = None
        body = None
        # getting links from file content
        if isinstance(text, str):
            body = text
            uri_list = text.split('\n')
        # getting links from list
        elif isinstance(text, List):
            body = '\n'.join(text)
            uri_list = text
        inner_html = decorators.decorate_uri_list(uri_list)
        return Attachment(body=body, mime=Mime.text_uri_list, inner_html=inner_html)
    except Exception as error:
        utils.log_error(None, "Error parsing uri list:", error)
        return Attachment(body="Error parsing uri list.", mime=Mime.text_plain)


def _attachment_image(data: bytes | str, mime: str) -> Attachment:
    """
    Returns an attachment object with bytes representing an image.
    """
    if not isinstance(data, (str, bytes)):
        msg = f"Error parsing image body of type '{type(data)}'"
        utils.log_error(None, msg)
        return Attachment(body=msg, mime=Mime.text_plain)
    if isinstance(data, str):
        try:
            data = base64.b64decode(data)
        except Exception as error:
            utils.log_error(None, "Error parsing image bytes:", error)
            return Attachment(body="Error parsing image bytes.", mime=Mime.text_plain)
    return Attachment(body=data, mime=mime)


def _attachment_video(data: bytes | str, mime: str) -> Attachment:
    """
    Returns an attachment object with bytes representing a video.
    """
    if not isinstance(data, (str, bytes)):
        msg = f"Error parsing video body of type '{type(data)}'"
        utils.log_error(None, msg)
        return Attachment(body=msg, mime=Mime.text_plain)
    if isinstance(data, str):
        try:
            data = base64.b64decode(data)
        except Exception as error:
            utils.log_error(None, "Error parsing video bytes:", error)
            return Attachment(body="Error parsing video bytes.", mime=Mime.text_plain)
    return Attachment(body=data, mime=mime)
