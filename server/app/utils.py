import logging
import re

from app.constants import LINK_HEADER_PATTERN

logger = logging.getLogger(__name__)


def parse_link_header(header_value: str) -> dict:
    """
    Example of what the value is for this header we want to parse

    <https://api.github.com/organizations/913567/members?page=1>; rel="prev",
    <https://api.github.com/organizations/913567/members?page=1>; rel="first"
    """
    d = {}
    for link_item in header_value.split(","):
        match = re.match(LINK_HEADER_PATTERN, link_item.strip())
        if match:
            link = match.group("link")
            rel = match.group("rel")
            d[rel] = link
        else:
            logger.error("No match for %s", link_item)

    return d
