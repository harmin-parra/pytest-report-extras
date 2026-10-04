import pytest
from typing import Literal, Optional
from .link import Link


#
# Marker related functions
#

def get_marker_links(
    item: pytest.Item,
    link_type: Literal["issue", "tms", "link"],
    fx_link_pattern: Optional[str] = None
) -> list[Link]:
    """
    Returns the urls and labels, as a list of tuples, of the links of a given marker.

    Args:
        item (pytest.Item): The test item.
        link_type: The marker name.
        fx_link_pattern: The link pattern of the marker's url.
    """
    if fx_link_pattern is None and link_type in ("issue", "tms"):
        return []
    links = []
    if link_type == "link":
        for marker in item.iter_markers(name=link_type):
            url = marker.args[0] if len(marker.args) > 0 else None
            text = marker.args[1] if len(marker.args) > 1 else None
            icon = marker.args[2] if len(marker.args) > 2 else None
            url = marker.kwargs.get("url", url)
            text = marker.kwargs.get("text", text)
            icon = marker.kwargs.get("icon", icon)
            if url not in (None, ''):
                text = url if text is None else text
                links.append(Link(url, text, link_type, icon))
    else:
        for marker in item.iter_markers(name=link_type):
            keys = marker.args[0] if len(marker.args) > 0 else ""
            keys = marker.kwargs.get("keys", keys)
            keys = keys.replace(' ', '').split(',') if len(keys) > 0 else []
            icon = marker.args[1] if len(marker.args) > 1 else None
            icon = marker.kwargs.get("icon", icon)
            for key in keys:
                if key not in (None, ''):
                    links.append(Link(fx_link_pattern.replace("{}", key), key, link_type, icon))

    return links


def get_all_markers_links(
    item: pytest.Item,
    fx_issue_link_pattern: Optional[str],
    fx_tms_link_pattern: Optional[str]
) -> list[Link]:
    """
    Returns the urls and labels, as a list of tuples, of the links of all markers (issue, tms and link).

    Args:
        item (pytest.Item): The test item.
        fx_issue_link_pattern: The link pattern for the "issues" marker.
        fx_tms_link_pattern: The link pattern for the "tms" marker.
    """
    links1 = get_marker_links(item, "issue", fx_issue_link_pattern)
    links2 = get_marker_links(item, "tms", fx_tms_link_pattern)
    links3 = get_marker_links(item, "link")
    return links1 + links2 + links3


def add_links(
    item: pytest.Item,
    extras,
    links: list[Link],
    fx_html: Optional[str],
    fx_allure: Optional[str],
    fx_links_column: Literal["all", "link", "issue", "tms", "none"] = "all"
) -> None:
    """
    Add links to the report.

    Args:
        item (pytest.Item): The test item.
        extras (List[pytest_html.extras.extra]): The test extras.
        links (List[tuple[str, str]]: The links to add.
        fx_html (str): The report_html fixture.
        fx_allure (str): The report_allure fixture.
        fx_links_column (str): The links_column fixture.
    """
    pytest_html = item.config.pluginmanager.getplugin("html")
    for link in links:
        if fx_html is not None and pytest_html is not None:
            if fx_links_column in ("all", link.type):
                extras.append(pytest_html.extras.url(link.url, name=f"{link.icon} {link.text}"))
        if fx_allure is not None:  # and item.config.pluginmanager.has_plugin("allure_pytest"):
            import allure
            from allure_commons.types import LinkType
            allure_link_type = None
            if link.type == "link":
                allure_link_type = LinkType.LINK
            if link.type == "issue":
                allure_link_type = LinkType.ISSUE
            if link.type == "tms":
                allure_link_type = LinkType.TEST_CASE
            allure.dynamic.link(url=link.url, link_type=allure_link_type, name=link.text)
