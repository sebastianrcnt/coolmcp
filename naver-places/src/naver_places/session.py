"""Session / credential sourcing — the single seam for Naver auth.

MCP tools and the model never touch cookie/token lifecycle. This module owns
where credentials come from (the user's logged-in Chrome profile) and caches
them briefly so every tool call does not re-hit the Chrome DB / macOS Keychain.

Profile is selected via the NAVER_CHROME_PROFILE environment variable
(default "Default").

Alternatively, set NAVER_COOKIES to a JSON object of cookie name→value pairs
to bypass Chrome entirely (useful when the GNOME Keyring is unavailable):
  export NAVER_COOKIES='{"NID_AUT": "...", "NNB": "..."}'
"""

import json
import os
import time

from .cookies import bootstrap_anonymous_cookies, get_naver_cookies
from .errors import NaverAuthError

PROFILE_ENV = "NAVER_CHROME_PROFILE"
# Set to "0"/"false" to disable the anonymous fallback and require Chrome cookies.
ANONYMOUS_ENV = "NAVER_ALLOW_ANONYMOUS"
_CACHE_TTL_SECONDS = 300.0
_ANON_KEY = "__anonymous__"

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

    If NAVER_COOKIES env var is set to a JSON object, it is used directly
    and Chrome is not consulted. Otherwise cookies are read from Chrome's
    on-disk database and cached for 5 minutes per profile.

    Raises NaverAuthError if no cookies can be obtained.
    """
    # Fast path: explicit cookie JSON from env var
    raw_cookies = os.environ.get("NAVER_COOKIES")
    if raw_cookies:
        try:
            return json.loads(raw_cookies)
        except json.JSONDecodeError as exc:
            raise NaverAuthError(
                f"NAVER_COOKIES is not valid JSON: {exc}"
            ) from exc

    profile = _current_profile()
    now = time.monotonic()

    if not force_refresh:
        cached = _cache.get(profile)
        if cached is not None and cached[0] > now:
            return cached[1]

    try:
        cookies = get_naver_cookies(profile)
    except Exception as exc:
        # Chrome cookies unavailable (e.g. locked keyring). Public Naver Maps
        # search/detail/reviews work anonymously, so fall back unless disabled.
        if not _anonymous_allowed():
            raise NaverAuthError(str(exc)) from exc
        return _get_anonymous_cookies(now)

    if not cookies:
        if _anonymous_allowed():
            return _get_anonymous_cookies(now)
        raise NaverAuthError(
            f"No Naver cookies found for Chrome profile '{profile}'. "
            f"Open Chrome with that profile and visit naver.com (log in for "
            f"personalized data), or set NAVER_CHROME_PROFILE to another profile."
        )

    _cache[profile] = (now + _CACHE_TTL_SECONDS, cookies)
    return cookies


def _anonymous_allowed() -> bool:
    return os.environ.get(ANONYMOUS_ENV, "1").lower() not in ("0", "false", "no")


def _get_anonymous_cookies(now: float) -> dict[str, str]:
    """Return cached anonymous cookies, bootstrapping a fresh jar if needed."""
    cached = _cache.get(_ANON_KEY)
    if cached is not None and cached[0] > now:
        return cached[1]
    cookies = bootstrap_anonymous_cookies()
    _cache[_ANON_KEY] = (now + _CACHE_TTL_SECONDS, cookies)
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
    except Exception as exc:  # e.g. locked keyring, profile directory not found
        anon_ok = _anonymous_allowed()
        return {
            "profile": profile,
            "cookieCount": 0,
            "mode": "anonymous" if anon_ok else "none",
            "hasNaverSession": False,
            "isLoggedIn": False,
            "publicToolsWork": anon_ok,
            "message": (
                "Could not read Chrome cookies "
                f"({type(exc).__name__}), but anonymous fallback is enabled — "
                "public search / detail / reviews WORK; only personalized tools "
                "are unavailable."
                if anon_ok
                else f"Could not read cookies and anonymous fallback is disabled: {exc}"
            ),
        }

    has_session = _BASELINE_COOKIE in cookies
    is_logged_in = _LOGIN_COOKIE in cookies
    anon_ok = _anonymous_allowed()

    if is_logged_in:
        mode = "logged_in"
        message = "Logged in — personalized data (following reviews, reactions) available."
    elif has_session:
        mode = "logged_in"
        message = (
            "Has a Naver session but not logged in — public search/reviews work; "
            "personalized data will be empty."
        )
    elif anon_ok:
        mode = "anonymous"
        message = (
            "No Chrome login session, but anonymous fallback is enabled — public "
            "search / place detail / visitor reviews WORK. Only personalized "
            "tools (following reviews) return empty."
        )
    else:
        mode = "none"
        message = "No Naver session for this profile — visit naver.com in this Chrome profile."

    # Public tools work whenever we have any session OR anonymous fallback is on.
    public_tools_work = has_session or is_logged_in or anon_ok

    return {
        "profile": profile,
        "cookieCount": len(cookies),
        "mode": mode,
        "hasNaverSession": has_session,
        "isLoggedIn": is_logged_in,
        "publicToolsWork": public_tools_work,
        "message": message,
    }
