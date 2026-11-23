"""Keenable 0.3.0-shaped fetch responses for offline stubs."""

from keenable import FetchResponse, Page
from keenable.models import FetchError


def fetch_response(url, content, published_at=None, *, truncated=False, error=None):
    """A FetchResponse with one page, as client.fetch(url) returns it."""
    page = Page(url=url, title="", content=content, published_at=published_at,
                truncated=truncated,
                error=FetchError(**error) if error else None)
    return FetchResponse(results=[page])
