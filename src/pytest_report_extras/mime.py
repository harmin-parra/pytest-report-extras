import re
from enum import StrEnum
from typing import Optional
from typing import Self


class Mime(StrEnum):
    """
    Enum to hold mime type values.
    """

    JSON = "application/json"
    XML = "application/xml"
    YAML = "application/yaml"
    BMP = "image/bmp"
    GIF = "image/gif"
    JPEG = "image/jpeg"
    PNG = "image/png"
    SVG = "image/svg+xml"
    IMAGE = "image/*"
    CSV = "text/csv"
    HTML = "text/html"
    TEXT = "text/plain"
    URI = "text/uri-list"
    VIDEO = "video/*"
    MP4 = "video/mp4"
    OGG = "video/ogg"
    OGV = "video/ogv"
    WEBM = "video/webm"

    @staticmethod
    def is_supported(mime: Optional[str]) -> bool:
        return mime in (
            Mime.JSON, Mime.XML, Mime.YAML,
            Mime.BMP, Mime.GIF, Mime.JPEG, Mime.PNG, Mime.SVG,
            Mime.CSV, Mime.HTML, Mime.TEXT, Mime.URI,
            Mime.MP4, Mime.OGG, Mime.OGV, Mime.WEBM
        )

    @staticmethod
    def is_unsupported(mime: Optional[str]) -> bool:
        return not Mime.is_supported(mime)

    @staticmethod
    def get_extension(mime: Optional[str]) -> Optional[str]:
        if mime in (None, Mime.URI, Mime.IMAGE, Mime.VIDEO):
            return None
        match mime:
            case Mime.TEXT:
                return "txt"
            case Mime.SVG:
                return "svg"
        if Mime.is_supported(mime):
            return mime[mime.index('/') + 1:]
        else:
            matcher = re.search(r"[./](?!.*[./])", mime)
            if matcher:
                return mime[matcher.start() + 1:]
            else:
                return mime

    @staticmethod
    def is_image(mime: Optional[str]) -> bool:
        return mime is not None and mime.startswith("image/")

    @staticmethod
    def is_image_binary(mime: Optional[str]) -> bool:
        """ Whether the mime type represents an image in binary format: png, mpeg, gif, tiff """
        return mime is not None and mime.startswith("image/") and not mime.startswith("image/svg")

    @staticmethod
    def is_video(mime: Optional[str]) -> bool:
        return mime is not None and mime.startswith("video/")

    @staticmethod
    def is_multimedia(mime: Optional[str]) -> bool:
        return Mime.is_image(mime) or Mime.is_video(mime)

    @staticmethod
    def is_not_image(mime: Optional[str]) -> bool:
        return not Mime.is_image(mime)

    @staticmethod
    def is_not_video(mime: Optional[str]) -> bool:
        return not Mime.is_video(mime)

    @staticmethod
    def is_not_multimedia(mime: Optional[str]) -> bool:
        return not Mime.is_multimedia(mime)

    @classmethod
    def get_mime(cls, value: Optional[str]) -> Optional[Self | str]:
        """
        Returns a mime type enum.
        
        Args:
            value (str): A mime-type or an extension.
        
        Returns:
            The mime type enum or None if the mime-type or extension is unsupported/unknown.
        """
        if value is None or not isinstance(value, str):
            return None
        value = value.lower()
        # value is a mime-type
        if value == "text/xml":
            return cls("application/xml")
        # value is an extension
        if value in ("text", "txt"):
            return cls("text/plain")
        if value == "svg":
            return cls("image/svg+xml")
        if value == "uri":
            return cls("text/uri-list")
        if value in ("json", "xml", "yaml"):
            return cls("application/" + value)
        if value in ("bmp", "gif", "jpeg", "png"):
            return cls("image/" + value)
        if value in ("csv", "html", "plain"):
            return cls("text/" + value)
        if value in ("mp4", "ogg", "ogv", "webm"):
            return cls("video/" + value)
        if '/' in value:
            try:
                return cls(value)
            except ValueError:
                pass
        # value is an unknown myme-type/extension
        # Find the last occurrence of '.' or '/'
        matcher = re.search(r"[./](?!.*[./])", value)
        if matcher:
            return value[matcher.start() + 1:]
        else:
            return value
