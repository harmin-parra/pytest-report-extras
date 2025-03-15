import base64
import csv
import io
import json
import re
import xml.dom.minidom as xdom
import yaml
from typing import List
from typing import Optional
from typing import Self
from . import decorators
from . import utils
from .mime import Mime


class Attachment:
    """
    Class to represent attachments.
    """

    def __init__(
        self,
        body: Optional[str | dict | list[str] | bytes] = None,
        source: Optional[str] = None,
        mime: Optional[Mime | str] = None,
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

    @classmethod
    def parse_body(
        cls,
        body: str | dict | list[str] | bytes,
        mime: Mime,
        indent: int = 4,
        delimiter=',',
        report=None
    ) -> Self:
        """
        Creates an attachment from the content/body.

        Args:
            body (str | dict | list[str] | bytes): The content/body of the body.
                Can be of type 'dict' for JSON mime type.
                Can be of type 'list[str]' for uri-list mime type.
                Can be of type 'bytes' for image mime type.
            mime (Mime): The mime type (optional).
            indent: The indent for XML, JSON and YAML attachments.
            delimiter (str): The delimiter for CSV documents.
            report (extras.Extras): The Extras report instance.

        Returns:
            An Attachment object representing the attachment.
        """
        if body in (None, ''):
            return cls(body="Attachment body is None or empty", mime=Mime.TEXT)
        if isinstance(body, List):
            mime = Mime.URI
        if Mime.is_image(mime):
            return _attachment_image(body, mime)
        if Mime.is_video(mime):
            return _attachment_video(body, mime)
        if Mime.is_unsupported(mime):
            return _attachment_unsupported(body, mime, report)
        match mime:
            case Mime.JSON:
                return _attachment_json(body, indent)
            case Mime.XML:
                return _attachment_xml(body, indent)
            case Mime.YAML:
                return _attachment_yaml(body, indent)
            case Mime.CSV:
                return _attachment_csv(body, delimiter=delimiter)
            case Mime.URI:
                return _attachment_uri_list(body)
            case Mime.HTML:
                return _attachment_html(body, report)
            case Mime.TEXT:
                return _attachment_txt(body)
            case _:
                return None

    @classmethod
    def parse_source(
        cls,
        source: str,
        mime: Mime,
        report
    ) -> Self:
        """
        Creates an attachment from a source file when mime is of type HTML or unsupported.

        Args:
            source (str): The filepath of the source.
            mime (Mime): The mime type (optional).
            report (extras.Extras): The Extras report instance.

        Returns:
            An Attachment object representing the attachment.
        """
        if source in (None, ''):
            return cls(body="Attachment source is None or empty", mime=Mime.TEXT)
        error_msg = f"Error creating attachment from source {source}"
        if Mime.is_unsupported(mime):
            inner_html = decorators.decorate_uri(
                utils.copy_file_and_get_link(report.fx_html, source, Mime.get_extension(mime), "downloads")
            )
            if inner_html == '':
                return Attachment(body=error_msg, mime=Mime.TEXT)
            else:
                return Attachment(source=source, inner_html=inner_html)
        elif mime == Mime.HTML:
            if report.fx_single_page:
                try:
                    f = open(source, 'r')
                    body = f.read()
                    f.close()
                    return _attachment_html(body, report)
                except Exception as error:
                    utils.log_error(None, f"{error_msg}: ", error)
                    return Attachment(body=f"{error_msg}\n{error}", mime=Mime.TEXT)
            else:
                inner_html = utils.copy_file_and_get_link(report.fx_html, source, "html", "sources")
                if inner_html != '':
                    return Attachment(source=source, mime=Mime.HTML, inner_html=inner_html)
                else:
                    return Attachment(body=error_msg, mime=Mime.TEXT)

    def __repr__(self) -> str:
        if isinstance(self.body, bytes):
            body_str = base64.b64encode(self.body).decode()
        else:
            body_str = self.body
        body_str = repr(body_str) if len(repr(body_str)) < 50 else repr(body_str)[:50] + "....'"
        inner_str = repr(self.inner_html) if len(repr(self.inner_html)) < 65 else repr(self.inner_html)[:65] + "....'"
        return (
            "{ " + f"body: {body_str}, source: {repr(self.source)}, "
                   f"mime: {repr(self.mime)}, inner_html: {inner_str}" + "}"
        )


def _attachment_json(text: str | dict, indent: int = 4) -> Attachment:
    """
    Returns an attachment object with a string holding a JSON document.
    """
    if not isinstance(text, (str, dict)):
        msg = f"Error parsing JSON body of type '{type(text)}'"
        utils.log_error(None, msg)
        return Attachment(body=msg, mime=Mime.TEXT)
    try:
        text = json.loads(text) if isinstance(text, str) else text
        return Attachment(body=json.dumps(text, indent=indent), mime=Mime.JSON)
    except Exception as error:
        utils.log_error(None, "Error formatting JSON:", error)
        return Attachment(body="Error formatting JSON:\n" + str(text), mime=Mime.TEXT)


def _attachment_xml(text: str, indent: int = 4) -> Attachment:
    """
    Returns an attachment object with a string holding an XML document.
    """
    if not isinstance(text, str):
        msg = f"Error parsing XML body of type '{type(text)}'"
        utils.log_error(None, msg)
        return Attachment(body=msg, mime=Mime.TEXT)
    try:
        result = (xdom.parseString(re.sub(r"\n\s+", '',  text).replace('\n', ''))
                  .toprettyxml(indent=" " * indent))
        result = '\n'.join(line for line in result.splitlines() if not re.match(r"^\s*<!--.*?-->\s*\n*$", line))
        return Attachment(body=result, mime=Mime.XML)
    except Exception as error:
        utils.log_error(None, "Error formatting XML:", error)
        return Attachment(body="Error formatting XML:\n" + str(text), mime=Mime.TEXT)


def _attachment_yaml(text: str, indent: int = 4) -> Attachment:
    """
    Returns an attachment object with a string holding a YAML document.
    """
    if not isinstance(text, str):
        msg = f"Error parsing YAML body of type '{type(text)}'"
        utils.log_error(None, msg)
        return Attachment(body=msg, mime=Mime.TEXT)
    try:
        text = yaml.safe_load(text)
        return Attachment(body=yaml.dump(text, indent=indent), mime=Mime.YAML)
    except Exception as error:
        utils.log_error(None, "Error formatting YAML:", error)
        return Attachment(body="Error formatting YAML:\n" + str(text), mime=Mime.TEXT)


def _attachment_txt(text: str) -> Attachment:
    """
    Returns an attachment object with a plain/text string.
    """
    if not isinstance(text, str):
        msg = f"Error parsing text body of type '{type(text)}'"
        utils.log_error(None, msg, None)
        return Attachment(body=msg, mime=Mime.TEXT)
    return Attachment(body=text, mime=Mime.TEXT)


def _attachment_csv(text: str, delimiter=',') -> Attachment:
    """
    Returns an attachment object with a string holding a CVS document.
    """
    if not isinstance(text, str):
        msg = f"Error parsing csv body of type '{type(text)}'"
        utils.log_error(None, msg)
        return Attachment(body=msg, mime=Mime.TEXT)
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
        return Attachment(body=text, mime=Mime.CSV, inner_html=inner_html)
    except Exception as error:
        utils.log_error(None, "Error formatting CSV:", error)
        return Attachment(body="Error formatting CSV:\n" + str(text), mime=Mime.TEXT)


def _attachment_uri_list(text: str | list[str]) -> Attachment:
    """
    Returns an attachment object with a uri list.
    """
    if not isinstance(text, (str, list)):
        msg = f"Error parsing uri-list body of type '{type(text)}'"
        utils.log_error(None, msg)
        return Attachment(body=msg, mime=Mime.TEXT)
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
        else:
            raise TypeError()
        inner_html = decorators.decorate_uri_list(uri_list)
        return Attachment(body=body, mime=Mime.URI, inner_html=inner_html)
    except Exception as error:
        utils.log_error(None, "Error parsing uri list:", error)
        return Attachment(body="Error parsing uri list.", mime=Mime.TEXT)


def _attachment_image(data: bytes | str, mime: str) -> Attachment:
    """
    Returns an attachment object with bytes representing an image.
    """
    if not isinstance(data, (str, bytes)):
        msg = f"Error parsing image body of type '{type(data)}'"
        utils.log_error(None, msg)
        return Attachment(body=msg, mime=Mime.TEXT)
    if isinstance(data, str):
        try:
            data = base64.b64decode(data)
        except Exception as error:
            utils.log_error(None, "Error parsing image bytes:", error)
            return Attachment(body="Error parsing image bytes.", mime=Mime.TEXT)
    return Attachment(body=data, mime=mime)


def _attachment_video(data: bytes | str, mime: str) -> Attachment:
    """
    Returns an attachment object with bytes representing a video.
    """
    if not isinstance(data, (str, bytes)):
        msg = f"Error parsing video body of type '{type(data)}'"
        utils.log_error(None, msg)
        return Attachment(body=msg, mime=Mime.TEXT)
    if isinstance(data, str):
        try:
            data = base64.b64decode(data)
        except Exception as error:
            utils.log_error(None, "Error parsing video bytes:", error)
            return Attachment(body="Error parsing video bytes.", mime=Mime.TEXT)
    return Attachment(body=data, mime=mime)


def _attachment_html(text: str, report):
    inner_html = None
    mime = Mime.HTML
    error_msg = "Error creating HTML attachment from body"
    if report.fx_html:
        if report.fx_single_page:
            try:
                encoded_bytes = base64.b64encode(text.encode("utf-8"))
                encoded_str = encoded_bytes.decode("utf-8")
                inner_html = f"data:text/html;base64,{encoded_str}"
            except Exception as error:
                text = f"{error_msg}\n{error}"
                mime = Mime.TEXT
                utils.log_error(None, error_msg, error)
        else:
            inner_html = utils.save_data_and_get_link(report.fx_html, text, "html", "sources")
            if inner_html == '':
                text = error_msg
                mime = Mime.TEXT
    return Attachment(body=text, mime=mime, inner_html=inner_html)


def _attachment_unsupported(text: str, mime, report):
    inner_html = None
    if report.fx_html:
        inner_html = decorators.decorate_uri(
            utils.save_data_and_get_link(report.fx_html, text, Mime.get_extension(mime), "downloads")
        )
        if inner_html == '':
            return Attachment(body="Error creating attachment from body", mime=Mime.TEXT)
    return Attachment(body=text, inner_html=inner_html)
