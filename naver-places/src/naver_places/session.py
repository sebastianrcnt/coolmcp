"""Session / credential sourcing — the single seam for Naver auth.

MCP tools and the model never touch cookie/token lifecycle. This module owns
where credentials come from (the user's logged-in Chrome profile) and caches
them briefly so every tool call does not re-hit the Chrome DB / macOS Keychain.

Profile is selected via the NAVER_CHROME_PROFILE environment variable
(default "Default").
"""

import os
import time

from .cookies import get_naver_cookies
from .errors import NaverAuthError

PROFILE_ENV = "NAVER_CHROME_PROFILE"
_CACHE_TTL_SECONDS = 300.0

# Cookie Naver sets on any visit; presence => the profile has a usable Naver
# session. NID_AUT presence => the user is actually logged in.
_BASELINE_COOKIE = "NNB"
_LOGIN_COOKIE = "NID_AUT"

# Per-process cache: {profile: (monotonic_expiry, cookies)}
_cache: dict[str, tuple[float, dict[str, str]]] = {}


def _current_profile() -> str:
    return os.environ.get(PROFILE_ENV, "Default")


def get_session_cookies(force_refresh: bool = False) -> dict[str, str]:
    """Return Naver session cookies for the configured Chrome profile.

    Cached up to 5 minutes per profile to avoid repeated Chrome/Keychain reads.
    Raises NaverAuthError if no cookies are found for the profile.
    """
    profile = _current_profile()
    now = time.monotonic()

    if not force_refresh:
        cached = _cache.get(profile)
        if cached is not None and cached[0] > now:
            return cached[1]

    cookies = get_naver_cookies(profile)
    if not cookies:
        raise NaverAuthError(
            f"No Naver cookies found for Chrome profile '{profile}'. "
            f"Open Chrome with that profile and visit naver.com (log in for "
            f"personalized data), or set NAVER_CHROME_PROFILE to another profile."
        )

    _cache[profile] = (now + _CACHE_TTL_SECONDS, cookies)
    return cookies


def clear_session_cache() -> None:
    """Drop all cached cookies (e.g. after a login or profile change)."""
    _cache.clear()


def check_naver_login(profile: str | None = None) -> dict:
    """Report auth status of a Chrome profile WITHOUT raising.

    Returns: profile, cookieCount, hasNaverSession (baseline cookie present),
    isLoggedIn (login cookie present), message.
    """
    profile = profile or _current_profile()
    try:
        cookies = get_naver_cookies(profile)
    except Exception as exc:  # e.g. profile directory not found
        return {
            "profile": profile,
            "cookieCount": 0,
            "hasNaverSession": False,
            "isLoggedIn": False,
            "message": f"Could not read cookies: {exc}",
        }

    has_session = _BASELINE_COOKIE in cookies
    is_logged_in = _LOGIN_COOKIE in cookies
    if is_logged_in:
        message = "Logged in — personalized data (following reviews, reactions) available."
    elif has_session:
        message = (
            "Has a Naver session but not logged in — public search/reviews work; "
            "personalized data will be empty."
        )
    else:
        message = "No Naver session for this profile — visit naver.com in this Chrome profile."

    return {
        "profile": profile,
        "cookieCount": len(cookies),
        "hasNaverSession": has_session,
        "isLoggedIn": is_logged_in,
        "message": message,
    }
