"""Chrome cookie reader for Naver domains.

Reads cookies directly from Chrome's SQLite database using the macOS Keychain
decryption key. Chrome does not need to be closed — SQLite WAL mode allows
concurrent reads while Chrome is running.
"""

from pycookiecheat import chrome_cookies

# Domains that Naver APIs are called against
_NAVER_DOMAINS = [
    "https://map.naver.com",
    "https://pcmap.place.naver.com",
    "https://pcmap-api.place.naver.com",
    "https://ncpt.naver.com",
]


def get_naver_cookies(chrome_profile: str | None = None) -> dict[str, str]:
    """Read Naver session cookies from the Chrome cookie database.

    Args:
        chrome_profile: Path to a Chrome profile directory. Defaults to the
                        system default profile.

    Returns:
        Merged dict of cookies for all Naver domains.
    """
    kwargs = {}
    if chrome_profile:
        kwargs["cookie_file"] = chrome_profile

    merged: dict[str, str] = {}
    for domain in _NAVER_DOMAINS:
        merged.update(chrome_cookies(domain, **kwargs))
    return merged
