"""Chrome cookie reader for Naver domains.

Reads cookies directly from Chrome's SQLite database. On macOS decryption uses
the Keychain; on Linux it uses GNOME Keyring / kwallet / a blank passphrase
(pycookiecheat handles this automatically). Chrome does not need to be closed —
SQLite WAL mode allows concurrent reads while Chrome is running.

Linux keyring note
------------------
If the GNOME Login keyring is locked (common in headless/SSH sessions), cookie
decryption will fail. Two remedies:

  1. Unlock before running:
       echo "YOUR_PASSWORD" | gnome-keyring-daemon --unlock

  2. Set the env var and let this module unlock automatically:
       export GNOME_KEYRING_PASSWORD=your_password
       naver-places auth
"""

import os
import platform
import subprocess
from pathlib import Path

from pycookiecheat import chrome_cookies


def _chrome_base() -> Path:
    if platform.system() == "Darwin":
        return Path.home() / "Library/Application Support/Google/Chrome"
    return Path.home() / ".config/google-chrome"


# Domains that Naver APIs are called against
_NAVER_DOMAINS = [
    "https://map.naver.com",
    "https://pcmap.place.naver.com",
    "https://pcmap-api.place.naver.com",
    "https://ncpt.naver.com",
]


def _try_unlock_keyring(password: str) -> bool:
    """Attempt to unlock the GNOME Login keyring via gnome-keyring-daemon.

    Returns True if the daemon accepted the password (exit code 0).
    """
    try:
        result = subprocess.run(
            ["gnome-keyring-daemon", "--unlock"],
            input=password.encode(),
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def unlock_keyring(password: str) -> bool:
    """Unlock the GNOME Keyring with a password. Returns True on success."""
    return _try_unlock_keyring(password)


def bootstrap_anonymous_cookies() -> dict[str, str]:
    """Get a fresh anonymous Naver session cookie jar — no login, no keyring.

    Naver Maps public search / place detail / visitor reviews all work without a
    logged-in account. This visits naver.com to collect whatever baseline session
    cookies (e.g. NNB) Naver hands out. Returns {} if the bootstrap request fails;
    the Naver endpoints tolerate an empty jar anyway.
    """
    import httpx

    ua = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
    )
    try:
        with httpx.Client(follow_redirects=True, headers={"user-agent": ua}, timeout=10) as c:
            c.get("https://www.naver.com/")
            c.get("https://map.naver.com/")
            return dict(c.cookies)
    except httpx.RequestError:
        return {}


def list_chrome_profiles() -> list[str]:
    """Return available Chrome profile names (e.g. ["Default", "Profile 4"])."""
    base = _chrome_base()
    if not base.exists():
        return []
    return sorted(
        p.name
        for p in base.iterdir()
        if (p / "Cookies").exists()
    )


def get_naver_cookies(profile: str = "Default") -> dict[str, str]:
    """Read Naver session cookies from a Chrome profile's cookie database.

    On Linux, if the GNOME Login keyring is locked, first checks
    GNOME_KEYRING_PASSWORD env var and attempts an automatic unlock.

    Args:
        profile: Chrome profile name, e.g. "Default", "Profile 4".
                 Run list_chrome_profiles() to see available profiles.

    Returns:
        Merged dict of cookies for all Naver domains.
    """
    cookie_file = _chrome_base() / profile / "Cookies"
    if not cookie_file.exists():
        raise FileNotFoundError(
            f"Cookie file not found: {cookie_file}\n"
            f"Available profiles: {list_chrome_profiles()}"
        )

    def _read() -> dict[str, str]:
        merged: dict[str, str] = {}
        for domain in _NAVER_DOMAINS:
            merged.update(chrome_cookies(domain, cookie_file=str(cookie_file)))
        return merged

    try:
        return _read()
    except Exception as exc:
        if "unlock" not in str(exc).lower() and "keyring" not in str(exc).lower():
            raise

        # Keyring is locked — try auto-unlock via env var
        kp = os.environ.get("GNOME_KEYRING_PASSWORD")
        if kp and _try_unlock_keyring(kp):
            try:
                return _read()
            except Exception:
                pass  # Fall through to helpful error

        raise RuntimeError(
            "GNOME Keyring is locked — Chrome cookies cannot be decrypted.\n\n"
            "Fix option 1 — unlock once in your shell:\n"
            "  echo 'YOUR_PASSWORD' | gnome-keyring-daemon --unlock\n\n"
            "Fix option 2 — set env var for automatic unlock:\n"
            "  export GNOME_KEYRING_PASSWORD=your_password\n"
            "  naver-places auth\n\n"
            "Fix option 3 — pass cookies as JSON via NAVER_COOKIES env var:\n"
            "  export NAVER_COOKIES='{\"NID_AUT\": \"...\", \"NNB\": \"...\"}'\n"
            "  naver-places search '검색어'\n"
        ) from exc
