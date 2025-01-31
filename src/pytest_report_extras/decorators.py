import pathlib
from typing import Literal
from typing import Optional
from .utils import escape_html


#
# Auxiliary functions for the report generation
#
def append_header(item, call, report, extras, pytest_html,
                  description_tag: Literal["h1", "h2", "h3", "p", "pre"]):
    """
    Decorates and appends the test description and execution exception trace, if any, to the report extras.

    Args:
        item (pytest.Item): The test item.
        call (pytest.CallInfo): Information of the test call.
        report (pytest.TestReport): The test report returned by pytest.
        extras (List[pytest_html.extras.extra]): The report extras.
        pytest_html (types.ModuleType): The pytest-html plugin.
        description_tag (str): The HTML tag to use.
    """
    # Append description
    description = item.function.__doc__ if hasattr(item, 'function') else None
    extras.append(pytest_html.extras.html(decorate_description(description, description_tag)))
    # Append parameters
    parameters = item.callspec.params if hasattr(item, 'callspec') else None
    extras.append(pytest_html.extras.html(decorate_parameters(parameters)))
    # Append exception info
    clazz = "extras_exception"
    # Catch explicit pytest.fail and pytest.skip calls
    if (
        hasattr(call, 'excinfo') and
        call.excinfo is not None and
        call.excinfo.typename in ('Failed', 'Skipped') and
        hasattr(call.excinfo.value, "msg")
    ):
        extras.append(pytest_html.extras.html(
            "<pre>"
            f'<span class="{clazz}">{escape_html(call.excinfo.typename)}</span><br>'
            f"reason = {escape_html(call.excinfo.value.msg)}"
            "</pre>"
            )
        )
    # Catch XFailed tests
    if report.skipped and hasattr(report, 'wasxfail'):
        extras.append(pytest_html.extras.html(
            "<pre>"
            f'<span class="{clazz}">XFailed</span><br>'
            f"reason = {escape_html(report.wasxfail)}"
            "</pre>"
            )
        )
    # Catch XPassed tests
    if report.passed and hasattr(report, 'wasxfail'):
        extras.append(pytest_html.extras.html(
            "<pre>"
            f'<span class="{clazz}">XPassed</span><br>'
            f"reason = {escape_html(report.wasxfail)}"
            "</pre>"
            )
        )
    # Catch explicit pytest.xfail calls and runtime exceptions in failed tests
    if (
        hasattr(call, 'excinfo') and
        call.excinfo is not None and
        call.excinfo.typename not in ('Failed', 'Skipped')
    ):
        extras.append(pytest_html.extras.html(
            "<pre>"
            f'<span class="{clazz}">Exception:</span><br>'
            f"{escape_html(call.excinfo.typename)}<br>"
            f"{escape_html(call.excinfo.value)}"
            "</pre>"
            )
        )


def get_table_row_tag(
    comment: str,
    image: str,
    source: str,
    attachment,
    single_page: bool,
    clazz="extras_comment"
) -> str:
    """
    Returns the HTML table row of a test step.

    Args:
        comment (str): The comment of the test step.
        image (str): The screenshot anchor element.
        source (str): The page source anchor element.
        attachment (Attachment): The attachment.
        single_page (bool): Whether to generate the HTML report in a single page.
        clazz (str): The CSS class to apply to the comment table cell.

    Returns:
        str: The <tr> element.
    """
    if comment is None:
        comment = ""
    if image is not None:
        comment = decorate_comment(comment, clazz)
        image = decorate_image(image, single_page)
        if source is not None:
            source = decorate_page_source(source)
            return (
                f"<tr>"
                f"<td>{comment}</td>"
                f'<td class="extras_td"><div class="extras_td_div">{image}<br>{source}</div></td>'
                f"</tr>"
            )
        else:
            return (
                f"<tr>"
                f"<td>{comment}</td>"
                f'<td class="extras_td"><div class="extras_td_div">{image}</div></td>'
                "</tr>"
            )
    else:  # attachment is not None
        comment += decorate_attachment(attachment)
        comment = decorate_comment(comment, clazz)
        return (
            f"<tr>"
            f'<td colspan="2">{comment}</td>'
            f"</tr>"
        )


def decorate_description(description, description_tag):
    if description is None:
        return ""
    description = escape_html(description).strip().replace('\n', "<br>")
    description = description.strip().replace('\n', "<br>")
    return f'<{description_tag} class="extras_description">{description}</{description_tag}>'


def decorate_parameters(parameters):
    """
    Applies a CSS style to the test parameters
    """
    if parameters is None:
        return ""
    content = f'<span class="extras_params_title">Parameters</span><br>'
    for key, value in parameters.items():
        content += f'<span class="extras_params_key">{key}</span><span class="extras_params_value">: {value}</span><br>'
    return content


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


def decorate_page_source(filename: Optional[str]) -> str:
    """ Applies CSS class to a page source anchor element. """
    if filename in (None, ''):
        return ""
    clazz = "extras_page_src"
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


def decorate_attachment(attachment) -> str:
    """ Applies CSS class to an attachment. """
    clazz_pre = "extras_pre"
    clazz_frm = "extras_iframe"
    if attachment is None:
        return ""
    attachment.body = '' if attachment.body in (None, '') else attachment.body
    attachment.inner_html = '' if attachment.inner_html in (None, '') else attachment.inner_html
    if attachment.body == '' and attachment.inner_html == '':
        return ""
    # downloadable file with unknown mime type
    if attachment.mime is None and attachment.inner_html is not None:
        return ' ' + attachment.inner_html
    if attachment.inner_html == '':
        return f'<pre class="{clazz_pre}">{escape_html(attachment.body)}</pre>'
    else:
        if attachment.mime == "text/html":
            return f'<iframe class="{clazz_frm}" src="{attachment.inner_html}"></iframe>'
        else:
            return f'<pre class="{clazz_pre}">{attachment.inner_html}</pre>'
