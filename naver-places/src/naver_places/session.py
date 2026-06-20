"""Session / credential sourcing — the single seam for Naver auth.

MCP tools and the model never touch cookie or token lifecycle. This module
owns where credentials come from. Today that is the user's logged-in Chrome
profile; if token refresh is ever needed it belongs here, not in the tools.

The Chrome profile is selected via the NAVER_CHROME_PROFILE environment
variable (default "Default"). Use list_chrome_profiles() to discover names.
"""

import os

from .cookies import get_naver_cookies

DEFAULT_PROFILE_ENV = "NAVER_CHROME_PROFILE"


def get_session_cookies() -> dict[str, str]:
    """Return Naver session cookies for the configured Chrome profile.

    Reads the profile name from the NAVER_CHROME_PROFILE env var
    (default "Default") and loads cookies from that profile's Chrome DB.
    """
    profile = os.environ.get(DEFAULT_PROFILE_ENV, "Default")
    return get_naver_cookies(profile)
