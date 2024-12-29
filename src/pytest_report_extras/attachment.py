import json
import re
import xml.parsers.expat as expat
import xml.dom.minidom as xdom
import yaml
from .utils import escape_html


class Mime:
    text_plain = "text/plain"
    application_json = "application/json"
    application_xml = "application/xml"
    application_yaml = "application/yaml"
    text_csv = 5
    text_tab_separated_values = 6
    text_uri_list = 7


class Attachment:
    """
    Class to represent text to be formatted as code-block in a <pre> HTML tag.
    """
    def __init__(self, text: str = None, mime: str = Mime.text_plain, inner_html: str = None):
        self.text = text
        self.mime = mime
        self.inner_html = inner_html
    
    def __str__(self):
        if self.text in (None, ""):
            return ""
        else:
            return f'<pre class="extras_pre">{escape_html(self.text)}</pre>'

    def get_escaped_text(self):
        return escape_html(self.text)
    
    def get_html_tag(self):
        if self.inner_html is None:
            if self.text in (None, ""):
                return ""
            else:
                return f'<pre class="extras_pre">{escape_html(self.text)}</pre>'
        else:
            return f'<pre class="extras_pre">{self.inner_html}</pre>'

    @classmethod
    def parse_text(cls, text: str = None, mime: str = Mime.text_plain, indent: int = 4):
        match mime:
            case Mime.application_json:
                return _format_json(text, indent)
            case Mime.application_xml:
                return _format_xml(text, indent)
            case Mime.application_yaml:
                return _format_yaml(text, indent)
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
        return Attachment(text="Error formatting JSON.\n " + text, mime=Mime.text_plain)


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
        return Attachment("Error formatting XML.\n " + text, Mime.text_plain)
    return Attachment(result, Mime.application_xml)


def _format_yaml(text: str, indent: int = 4) -> Attachment:
    """
    Formats a string holding a YAML document.
    """
    try:
        text = yaml.safe_load(text)
        return Attachment(yaml.dump(text, indent=indent), Mime.application_yaml)
    except:
        return Attachment("Error formatting YAML.\n " + text, Mime.text_plain)


def _format_txt(text: str, mime: str = Mime.text_plain) -> Attachment:
    return Attachment(text, mime)


def _format_csv(text: str) -> Attachment:
    pass
