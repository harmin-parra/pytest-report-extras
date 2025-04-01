import pathlib
from typing import Optional
from _pytest.outcomes import Failed
from _pytest.outcomes import Skipped
from _pytest.outcomes import XFailed
from . import utils
from .link import Link
from .status import Status


#
# Auxiliary functions for the report generation
#
def get_header_rows(item, call, report, links, status: Status):
    """
    Decorates and appends the test description and execution exception trace, if any, to the report extras.

    Args:
        item (pytest.Item): The test item.
        call (pytest.CallInfo): Information of the test call.
        report (pytest.TestReport): The pytest test report.
        links (List[Link]): The links to add to the header.
        status (Status): The test execution status.
    """
    return (
        get_status_row(call, report, status) +
        get_description_row(item) +
        get_parameters_row(item) +
        get_exception_row(call) +
        get_links_row(links)
    )


def get_status_row(call, report, status):
    """ HTML table row for the test execution status and reason (if applicable). """
    reason = decorate_reason(call, report, status)
    return (
        '<tr class="visibility_status">'
        f'<td style="border: 0px"><span class="extras_status extras_status_{status}">{status.capitalize()}</span></td>'
        '<td class="extras_header_middle" style="border: 0px"></td>'
        f'<td style="border: 0px" class="extras_status_reason">{reason}</td>'
        "</tr>"
    )


def get_description_row(item):
    """ HTML table row for the test description. """
    row = ""
    description = item.function.__doc__ if hasattr(item, "function") else None
    if description is not None:
        row = (
            "<tr>"
            f'<td style="border: 0px"><span class="extras_title">Description</span></td>'
            '<td class="extras_header_middle" style="border: 0px"></td>'
            f'<td style="border: 0px">{decorate_description(description)}</td>'
            "</tr>"
        )
    return row


def get_parameters_row(item):
    """ HTML table row for the test parameters. """
    row = ""
    parameters = item.callspec.params if hasattr(item, "callspec") else None
    if parameters is not None:
        row = (
            '<tr class="visibility_parameters">'
            f'<td style="border: 0px"><span class="extras_title">Parameters</span></td>'
            '<td class="extras_header_middle" style="border: 0px"></td>'
            f'<td style="border: 0px">{decorate_parameters(parameters)}</td>'
            "</tr>"
        )
    return row


def get_exception_row(call):
    """ HTML table row for the test execution exception. """
    row = ""
    exception = decorate_exception(call)
    if exception != "":
        row = (
            "<tr>"
            f'<td style="border: 0px"><span class="extras_title">Exception</span></td>'
            '<td class="extras_header_middle" style="border: 0px"></td>'
            f'<td style="border: 0px">{exception}</td>'
            "</tr>"
        )
    return row


def get_links_row(links):
    """ HTML table row for the test links. """
    row = ""
    if len(links) > 0:
        row = (
            '<tr class="visibility_links">'
            f'<td style="border: 0px"><span class="extras_title">Links</span></td>'
            '<td class="extras_header_middle" style="border: 0px"></td>'
            f'<td style="border: 0px">{decorate_links(links)}</td>'
            "</tr>"
        )
    return row


def get_step_row(
    comment: str,
    multimedia: str,
    source: str,
    attachment,
    single_page: bool,
    clazz="extras_font extras_color_comment",
    clazz_row=None
) -> str:
    """
    Returns the HTML table row of a test step.

    Args:
        comment (str): The comment of the test step.
        multimedia (str): The image, video or audio anchor element.
        source (str): The page source anchor element.
        attachment (Attachment): The attachment.
        single_page (bool): Whether to generate the HTML report in a single page.
        clazz_row (str): The CSS class to apply to the comment table row.
        clazz (str): The CSS class to apply to the comment table cell.

    Returns:
        str: The <tr> element.
    """
    if comment is None:
        comment = ""
    clazz_row_str = ""
    if clazz_row is not None:
        clazz_row_str = f'class="{clazz_row}"'
    if multimedia is not None:
        comment = decorate_comment(comment, clazz)
        if attachment is not None and attachment.mime is not None:
            if attachment.mime.startswith("image/svg"):
                multimedia = decorate_image_svg(multimedia, attachment.body, single_page)
            elif attachment.mime.startswith("video/"):
                multimedia = decorate_video(multimedia, attachment.mime)
            elif attachment.mime.startswith("audio/"):
                multimedia = decorate_audio(multimedia, attachment.mime)
            else:  # Assuming mime = "image/*
                multimedia = decorate_image(multimedia, single_page)
        else:  # Multimedia with attachment = None are considered as images
            multimedia = decorate_image(multimedia, single_page)
        if source is not None:
            source = decorate_page_source(source)
            return (
                f'<tr {clazz_row_str}>'
                f"<td>{comment}</td>"
                f'<td class="extras_td"><div class="extras_td_div">{multimedia}<br>{source}</div></td>'
                f"</tr>"
            )
        else:
            return (
                f'<tr {clazz_row_str}>'
                f"<td>{comment}</td>"
                f'<td class="extras_td"><div class="extras_td_div">{multimedia}</div></td>'
                "</tr>"
            )
    else:
        comment = decorate_comment(comment, clazz)
        comment += decorate_attachment(attachment)
        return (
            f'<tr {clazz_row_str}>'
            f'<td colspan="2">{comment}</td>'
            f"</tr>"
        )


def decorate_description(description) -> str:
    """  Applies a CSS style to the test description. """
    if description is None:
        return ""
    description = utils.escape_html(description).strip().replace('\n', "<br>")
    description = description.strip().replace('\n', "<br>")
    return f'<pre class="extras_description extras_block">{description}</pre>'


def decorate_parameters(parameters) -> str:
    """ Applies a CSS style to the test parameters. """
    if parameters is None:
        return ""
    content = ""
    for key, value in parameters.items():
        content += f'<span class="extras_params_key">{key}</span><span class="extras_params_value">: {value}</span><br>'
    return content


def decorate_exception(call) -> str:
    """  Applies a CSS style to the test execution exception. """
    content = ""
    # Get runtime exceptions in failed tests
    if (
        hasattr(call, "excinfo") and
        call.excinfo is not None and
        not isinstance(call.excinfo.value, (Failed, XFailed, Skipped))
    ):
        content = content + (
            f'<pre class="extras_block">{utils.escape_html(call.excinfo.typename)}</pre><br>'
            f'<pre class="extras_block">{utils.escape_html(call.excinfo.value)}</pre>'
        )
    return content


def decorate_reason(call, report, status: Status) -> str:
    reason = ""
    # Get Xfailed and Xpassed tests
    if status in (Status.XFAILED, Status.XPASSED):
        reason = utils.escape_html(report.wasxfail)
    # Get explicit pytest.fail and pytest.skip calls
    if (
        hasattr(call, "excinfo") and
        call.excinfo is not None and
        isinstance(call.excinfo.value, (Failed, Skipped)) and
        hasattr(call.excinfo.value, "msg")
    ):
        reason = utils.escape_html(call.excinfo.value.msg)
    if reason != "":
        reason = "Reason: " + reason
    return reason


def decorate_links(links: list[Link]):
    """ Applies CSS style to a list of links """
    anchors = []
    for link in links:
        anchors.append(f'<a href="{link.url}" target="_blank" rel="noopener noreferrer">{link.icon} {link.label}</a>')
    return " , ".join(anchors)


def decorate_comment(comment, clazz) -> str:
    """
    Applies a CSS style to a text.

    Args:
        comment (str): The text to decorate.
        clazz (str): The CSS class to apply.

    Returns:
        The <span> element decorated with the CSS class.
    """
    if comment in (None, ''):
        return ""
    return f'<span class="{clazz}">{comment}</span>'


'''
def decorate_anchors(image, source):
    """ Applies CSS style to a screenshot and page source anchor elements. """
    if image is None:
        return ''
    image = decorate_image(image)
    if source is not None:
        source = decorate_page_source(source)
        return f'<div class="extras_div">{image}<br>{source}</div>'
    else:
        return image
'''


def decorate_image(uri: Optional[str], single_page: bool) -> str:
    """ Applies CSS class to an image anchor element. """
    if single_page:
        return decorate_image_from_base64(uri)
    else:
        return decorate_image_from_file(uri)


def decorate_image_from_file(uri: Optional[str]) -> str:
    clazz = "extras_image"
    if uri in (None, ''):
        return ""
    return f'<a href="{uri}" target="_blank" rel="noopener noreferrer"><img src ="{uri}" class="{clazz}"></a>'


def decorate_image_from_base64(uri: Optional[str]) -> str:
    clazz = "extras_image"
    if uri in (None, ''):
        return ""
    return f'<img src ="{uri}" class="{clazz}">'


def decorate_image_svg(uri: Optional[str], inner_html: Optional[str], single_page) -> str:
    """ Applies CSS class to an SVG element. """
    if uri in (None, '') or inner_html in (None, ''):
        return ""
    if single_page:
        return inner_html
    else:
        return f'<a href="{uri}" target="_blank" rel="noopener noreferrer">{inner_html}</a>'


def decorate_page_source(filename: Optional[str]) -> str:
    """ Applies CSS class to a page source anchor element. """
    clazz = "extras_page_src"
    if filename in (None, ''):
        return ""
    return f'<a href="{filename}" target="_blank" rel="noopener noreferrer" class="{clazz}">[page source]</a>'


def decorate_uri(uri: Optional[str]) -> str:
    """ Applies CSS class to a uri anchor element. """
    if uri in (None, ''):
        return ""
    if uri.startswith("downloads"):
        return f'<a href="{uri}" target="_blank" rel="noopener noreferrer">{pathlib.Path(uri).name}</a>'
    else:
        return f'<a href="{uri}" target="_blank" rel="noopener noreferrer">{uri}</a>'


def decorate_uri_list(uris: list[str]) -> str:
    """ Applies CSS class to a list of uri attachments. """
    links = ""
    for uri in uris:
        if uri not in (None, ''):
            links += decorate_uri(uri) + "<br>"
    return links


def decorate_video(uri: Optional[str], mime: str) -> str:
    """ Applies CSS class to a video anchor element. """
    clazz = "extras_video"
    if uri in (None, ''):
        return ""
    return (
        f'<video controls class="{clazz}">'
        f'<source src="{uri}" type="{mime}">'
        "Your browser does not support the video tag."
        "</video>"
    )


def decorate_audio(uri: Optional[str], mime: str) -> str:
    """ Applies CSS class to aa audio anchor element. """
    clazz = "extras_audio"
    if uri in (None, ''):
        return ""
    return (
        f'<audio controls class="{clazz}">'
        f'<source src="{uri}" type="{mime}">'
        "Your browser does not support the audio tag."
        "</audio>"
    )


def decorate_attachment(attachment) -> str:
    """ Applies CSS class to an attachment. """
    clazz_pre = "extras_attachment"
    clazz_frm = "extras_iframe"
    if attachment is None or (attachment.body in (None, '') and attachment.inner_html in (None, '')):
        return ""

    if attachment.inner_html is not None:
        if attachment.mime is None:  # downloadable file with unknown mime type
            return ' ' + attachment.inner_html
        if attachment.mime == "text/html":
            return f'<br><iframe class="{clazz_frm}" src="{attachment.inner_html}"></iframe>'
        else:  # text/csv, text/uri-list
            return f'<pre class="{clazz_pre}">{attachment.inner_html}</pre>'
    else:  # application/*, text/plain
        return f'<pre class="{clazz_pre}">{utils.escape_html(attachment.body)}</pre>'
