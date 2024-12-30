import csv
import io
import json
import re
import xml.parsers.expat as expat
import xml.dom.minidom as xdom
import yaml


class Mime:
    text_plain = "text/plain"
    application_json = "application/json"
    application_xml = "application/xml"
    application_yaml = "application/yaml"
    text_csv = "text/csv"
    text_uri_list = "text/uri-list"


class Attachment:
    """
    Class to represent text to be formatted as code-block in a <pre> HTML tag.
    """
    def __init__(self, text: str = None, mime: str = Mime.text_plain, inner_html: str = None):
        self.text = text
        self.mime = mime
        self.inner_html = inner_html

    @classmethod
    def parse_text(cls, text: str = None, mime: str = Mime.text_plain, indent: int = 4, delimiter=','):
        match mime:
            case Mime.application_json:
                return _format_json(text, indent)
            case Mime.application_xml:
                return _format_xml(text, indent)
            case Mime.application_yaml:
                return _format_yaml(text, indent)
            case Mime.text_csv:
                return _format_csv(text=text, delimiter=delimiter)
            case _:
                return _format_txt(text)


def _format_json(text: str, indent: int = 4) -> (str, str):
    """
    Formats a string holding a JSON document.
    """
    try:
        text = json.loads(text)
        return Attachment(text=json.dumps(text, indent=indent), mime=Mime.application_json)
    except:
        return Attachment(text="Error formatting JSON.\n" + text, mime=Mime.text_plain)


def _format_xml(text: str, indent: int = 4) -> Attachment:
    """
    Formats a string holding an XML document.
    """
    result = None
    try:
        result = xdom.parseString(re.sub(r"\n\s+", '',  text).replace('\n', '')).toprettyxml(indent=" " * indent)
        result = '\n'.join(line for line in result.splitlines() if not re.match(r"^\s*<!--.*?-->\s*\n*$", line))
    except expat.ExpatError:
        if text is None:
            text = 'None'
        return Attachment("Error formatting XML.\n" + text, Mime.text_plain)
    return Attachment(result, Mime.application_xml)


def _format_yaml(text: str, indent: int = 4) -> Attachment:
    """
    Formats a string holding a YAML document.
    """
    try:
        text = yaml.safe_load(text)
        return Attachment(yaml.dump(text, indent=indent), Mime.application_yaml)
    except:
        return Attachment("Error formatting YAML.\n" + text, Mime.text_plain)


def _format_txt(text: str, mime: str = Mime.text_plain) -> Attachment:
    return Attachment(text, mime)


def _format_csv(text: str, delimiter=',') -> Attachment:
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
        return Attachment("Error formatting YAML.\n" + text, Mime.text_plain)
    return Attachment(text, Mime.text_csv, inner_html)
