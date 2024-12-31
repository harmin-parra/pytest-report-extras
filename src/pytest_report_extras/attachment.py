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
    Class to hold mime type enums.
    """
    text_plain = "text/plain"
    text_html = "text/html"
    application_json = "application/json"
    application_xml = "application/xml"
    application_yaml = "application/yaml"
    text_csv = "text/csv"
    text_uri_list = "text/uri-list"


class Attachment:
    """
    Class to represent text to be formatted as code-block in a <pre> HTML tag.
    """
    def __init__(self, body: str = None, source: str = None, mime: str = None, inner_html: str = None):
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
        match mime:
            case Mime.application_json:
                return _format_json(body, indent)
            case Mime.application_xml:
                return _format_xml(body, indent)
            case Mime.application_yaml:
                return _format_yaml(body, indent)
            case Mime.text_csv:
                return _format_csv(body, delimiter=delimiter)
            case Mime.text_uri_list:
                return _format_uri_list(body)
            case _:
                return _format_txt(body)


def _format_json(text: str | Dict, indent: int = 4) -> Attachment:
    """
    Returns an attachment object with a string holding a JSON document.
    """
    try:
        text = json.loads(text) if isinstance(text, str) else text
        return Attachment(body=json.dumps(text, indent=indent), mime=Mime.application_json)
    except:
        return Attachment(body="Error formatting JSON.\n" + str(text), mime=Mime.text_plain)


def _format_xml(text: str, indent: int = 4) -> Attachment:
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


def _format_yaml(text: str, indent: int = 4) -> Attachment:
    """
    Returns an attachment object with a string holding a YAML document.
    """
    try:
        text = yaml.safe_load(text)
        return Attachment(body=yaml.dump(text, indent=indent), mime=Mime.application_yaml)
    except:
        return Attachment(body="Error formatting YAML.\n" + str(text), mime=Mime.text_plain)


def _format_txt(text: str) -> Attachment:
    """
    Returns an attachment object with a plain/body string.
    """
    return Attachment(body=text, mime=Mime.text_plain)


def _format_csv(text: str, delimiter=',') -> Attachment:
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


def _format_uri_list(text: str | List[str]) -> Attachment:
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
