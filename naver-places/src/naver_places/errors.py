"""Typed errors for the naver-places server.

These give MCP tool callers (and the model) a clean, actionable message instead
of a raw httpx/pydantic stack trace.
"""


class NaverPlacesError(Exception):
    """Base class for all naver-places errors."""


class NaverAuthError(NaverPlacesError):
    """Session cookies are missing or invalid.

    Usually means the selected Chrome profile has never been used with Naver,
    the profile name is wrong, or (for personalized data) you are not logged in.
    """


class NaverAPIError(NaverPlacesError):
    """A Naver API call failed — an HTTP error, a network error, or a GraphQL
    `errors` array in the response body."""
