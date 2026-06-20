"""Chrome cookie reader for Naver domains.

Reads cookies directly from Chrome's SQLite database using the macOS Keychain
decryption key. Chrome does not need to be closed — SQLite WAL mode allows
concurrent reads while Chrome is running.
"""

from pathlib import Path

from pycookiecheat import chrome_cookies

_CHROME_BASE = Path.home() / "Library/Application Support/Google/Chrome"

# Domains that Naver APIs are called against
_NAVER_DOMAINS = [
    "https://map.naver.com",
    "https://pcmap.place.naver.com",
    "https://pcmap-api.place.naver.com",
    "https://ncpt.naver.com",
]


def list_chrome_profiles() -> list[str]:
    """Return available Chrome profile names (e.g. ["Default", "Profile 4"])."""
    return sorted(
        p.name
        for p in _CHROME_BASE.iterdir()
        if (p / "Cookies").exists()
    )


def get_naver_cookies(profile: str = "Default") -> dict[str, str]:
    """Read Naver session cookies from a Chrome profile's cookie database.

    Args:
        profile: Chrome profile name, e.g. "Default", "Profile 4".
                 Run list_chrome_profiles() to see available profiles.

    Returns:
        Merged dict of cookies for all Naver domains.
    """
    cookie_file = _CHROME_BASE / profile / "Cookies"
    if not cookie_file.exists():
        raise FileNotFoundError(
            f"Cookie file not found: {cookie_file}\n"
            f"Available profiles: {list_chrome_profiles()}"
        )

    merged: dict[str, str] = {}
    for domain in _NAVER_DOMAINS:
        merged.update(chrome_cookies(domain, cookie_file=str(cookie_file)))
    return merged
