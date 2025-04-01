from typing import Literal


class Link:

    icons = {
        "link": "&#127760;",
        "issue": "&#128030;",
        "tms": "&#128203;",
    }

    def __init__(self, url: str, label: str, link_type: Literal["link", "issue", "tms"] = "link"):
        self.url = url
        self.label = label
        self.name = self.label
        self.type = link_type
        self.icon = Link.icons[link_type]

    def __repr__(self):
        return "{" + f"url: {self.url}, label: {self.label}, type: {self.type}, icon: {self.icon}" + "}"
