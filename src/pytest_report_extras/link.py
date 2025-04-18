from typing import Literal, Optional


class Link:

    icons = {
        "link": "&#127758;",
        "issue": "&#128030;",
        "tms": "&#128221;",
    }

    def __init__(self, url: str, label: str, link_type: Literal["link", "issue", "tms"] = "link", icon: Optional[str] = None):
        self.url = url
        self.label = label
        self.name = self.label
        self.type = link_type
        self.icon = icon if icon is not None else Link.icons[link_type]

    def __repr__(self):
        return "{" + f"url: {self.url}, label: {self.label}, type: {self.type}, icon: {self.icon}" + "}"
