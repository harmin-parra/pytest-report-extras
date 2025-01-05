import base64
import csv
import io
import json
import re
import xml.parsers.expat as expat
import xml.dom.minidom as xdom
import yaml
from typing import Dict
from typing import List
from . import utils


class Mime:
    """
    Class to hold mime type values.
    """
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
    application_json = "application/json"
    application_xml = "application/xml"
    application_yaml = "application/yaml"
    
    @staticmethod
    def isknown(mime: str):
        return mime in (Mime.image_bmp, Mime.image_gif, Mime.image_jpeg, Mime.image_png,
                        Mime.image_svg_xml, mime == Mime.image_tiff, Mime.text_csv,
                        Mime.text_html, Mime.text_plain, Mime.text_uri_list, Mime.application_json,
                        Mime.application_xml, Mime.application_yaml)

    @staticmethod
    def isunknown(mime: str):
        return not Mime.isknown(mime)

    @staticmethod
    def isimage(mime: str):
        return mime is not None and mime.startswith("image/")


class Attachment:
    """
    Class to represent attachments.
    """
    def __init__(
        self,
        body: str | List[str] | bytes = None,
        source: str = None,
        mime: str = None,
        inner_html: str = None
    ):
        self.body = body
        self.source = source
        self.mime = mime
        self.inner_html = inner_html

    @staticmethod
    def parse_body(
        body: str | List[str] = None,
        mime: str = Mime.text_plain,
        indent: int = 4,
        delimiter=',',
    ):
        if body is not None and isinstance(body, List):
            mime = Mime.text_uri_list
        if Mime.isimage(mime):
            return _attachment_image(body, mime)
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


def _attachment_json(text: str | Dict, indent: int = 4) -> Attachment:
    """
    Returns an attachment object with a string holding a JSON document.
    """
    try:
        text = json.loads(text) if isinstance(text, str) else text
        return Attachment(body=json.dumps(text, indent=indent), mime=Mime.application_json)
    except:
        return Attachment(body="Error formatting JSON.\n" + str(text), mime=Mime.text_plain)


def _attachment_xml(text: str, indent: int = 4) -> Attachment:
    """
    Returns an attachment object with a string holding an XML document.
    """
    result = None
    try:
        result = xdom.parseString(re.sub(r"\n\s+", '',  text).replace('\n', '')).toprettyxml(indent=" " * indent)
        result = '\n'.join(line for line in result.splitlines() if not re.match(r"^\s*<!--.*?-->\s*\n*$", line))
    except expat.ExpatError:
        if text is None:
            text = 'None'
        return Attachment(body="Error formatting XML.\n" + str(text), mime=Mime.text_plain)
    return Attachment(body=result, mime=Mime.application_xml)


def _attachment_yaml(text: str, indent: int = 4) -> Attachment:
    """
    Returns an attachment object with a string holding a YAML document.
    """
    try:
        text = yaml.safe_load(text)
        return Attachment(body=yaml.dump(text), mime=Mime.application_yaml)
    except:
        return Attachment(body="Error formatting YAML.\n" + str(text), mime=Mime.text_plain)


def _attachment_txt(text: str) -> Attachment:
    """
    Returns an attachment object with a plain/body string.
    """
    return Attachment(body=text, mime=Mime.text_plain)


def _attachment_csv(text: str, delimiter=',') -> Attachment:
    """
    Returns an attachment object with a string holding a CVS document.
    """
    inner_html = None
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
    except:
        return Attachment(body="Error formatting CSV.\n" + str(text), mime=Mime.text_plain)
    return Attachment(body=text, mime=Mime.text_csv, inner_html=inner_html)


def _attachment_uri_list(text: str | List[str]) -> Attachment:
    """
    Returns an attachment object with a uri list.
    """
    try:
        uri_list = None
        body = None
        if isinstance(text, str):
            body = text
            uri_list = text.split('\n')
        elif isinstance(text, List):
            body = '\n'.join(text)
            uri_list = text
        inner_html = utils.decorate_uri_list(uri_list)
        return Attachment(body=body, mime=Mime.text_uri_list, inner_html=inner_html)
    except:
        return Attachment(body="Error parsing uri list.", mime=Mime.text_plain)


def _attachment_image(data: bytes | str, mime: Mime) -> Attachment:
    """
    Returns an attachment object with bytes representing an image.
    """
    if isinstance(data, str):
        try:
            data = base64.b64decode(data)
        except:
            return Attachment(body="Error parsing image bytes.", mime=Mime.text_plain)
    return Attachment(body=data, mime=mime)
