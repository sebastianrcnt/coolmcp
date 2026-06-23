"""Command-line interface for naver-places."""

import asyncio
import json
import sys

import click

from .client import (
    get_following_reviews,
    get_photo_viewer,
    get_review_photos,
    get_theme_lists,
    get_visitor_reviews,
    search_places as _search_places,
)
from .cookies import list_chrome_profiles
from .html import fetch_place_detail
from .session import check_naver_login, get_session_cookies
from . import views


# ── helpers ──────────────────────────────────────────────────────────────────

def _json_out(data) -> None:
    click.echo(json.dumps(data, ensure_ascii=False, indent=2))


def _err(msg: str) -> None:
    click.echo(click.style(f"Error: {msg}", fg="red"), err=True)
    sys.exit(1)


def _star(score) -> str:
    try:
        f = float(score)
        filled = round(f / 5 * 5)
        return "★" * filled + "☆" * (5 - filled) + f"  {f:.1f}"
    except (TypeError, ValueError):
        return str(score)


# ── CLI root ─────────────────────────────────────────────────────────────────

@click.group()
def cli():
    """Naver Maps place search and info tool."""


# ── auth ─────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--profile", default=None, help="Chrome profile name (default: $NAVER_CHROME_PROFILE or 'Default')")
@click.option("--unlock-keyring", "keyring_pw", default=None, envvar="GNOME_KEYRING_PASSWORD",
              help="GNOME Keyring password to unlock before reading cookies (or set GNOME_KEYRING_PASSWORD)")
def auth(profile, keyring_pw):
    """Check Naver login status for a Chrome profile."""
    if keyring_pw:
        from .cookies import unlock_keyring
        ok = unlock_keyring(keyring_pw)
        status = "unlocked" if ok else "unlock failed"
        click.echo(click.style(f"  Keyring: {status}", fg="green" if ok else "red"))

    result = check_naver_login(profile)
    if result["isLoggedIn"]:
        icon, color = "✓", "green"
    elif result["publicToolsWork"]:
        icon, color = "~", "yellow"
    else:
        icon, color = "✗", "red"
    click.echo(click.style(f"{icon} {result['message']}", fg=color))
    click.echo(f"  Profile        : {result['profile']}")
    click.echo(f"  Mode           : {result['mode']}")
    click.echo(f"  Public tools   : {'work' if result['publicToolsWork'] else 'unavailable'}")
    click.echo(f"  Logged in      : {result['isLoggedIn']}")
    click.echo(f"  Cookie count   : {result['cookieCount']}")
    if not result["isLoggedIn"]:
        click.echo(click.style(
            "\n  Note: personalized tools (following reviews) need a Chrome login.\n"
            "  If keyring is locked and you want it, run:\n"
            "    echo 'PASSWORD' | gnome-keyring-daemon --unlock", fg="bright_black"
        ))


# ── profiles ──────────────────────────────────────────────────────────────────

@cli.command()
def profiles():
    """List Chrome profiles that have a Naver cookie database."""
    names = list_chrome_profiles()
    if not names:
        click.echo("No Chrome profiles with Naver cookies found.")
        return
    for name in names:
        click.echo(f"  {name}")


# ── search ────────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("query")
@click.option("--coords", default=None, metavar="LAT,LNG",
              help="Explicit center for distance ranking (default: Seoul City Hall)")
@click.option("--near", default=None, metavar="LANDMARK",
              help="Landmark/area to search around, auto-geocoded (e.g. 성균관대)")
@click.option("--enrich", is_flag=True,
              help="Attach rating/keywords to the top results (one call, no per-place detail)")
@click.option("--top", default=3, show_default=True, help="How many results to enrich with --enrich")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON")
def search(query, coords, near, enrich, top, as_json):
    """Search Naver Maps for places matching QUERY.

    QUERY should be a short keyword (dish/business name), not a sentence.
    Put the location in --near, not in QUERY.

    Example: naver-places search "순두부찌개" --near "성균관대" --enrich
    """
    async def _run():
        try:
            cookies = get_session_cookies()
        except Exception as exc:
            _err(str(exc))
        items, _used = await _search_places(query, cookies, coords=coords, near=near)
        if enrich:
            from .client import enrich_places
            pairs = await enrich_places(items, cookies, top=top)
            return views.enriched_search_results(pairs)
        return views.search_results(items)

    results = asyncio.run(_run())

    if as_json:
        _json_out(results)
        return

    if not results:
        click.echo("No results found.")
        return

    click.echo(click.style(f"\n검색 결과: {query}  ({len(results)}건)\n", bold=True))
    for i, r in enumerate(results, 1):
        dist_str = f"📍 {r['distanceKm']:.2f} km" if r["distanceKm"] else ""
        click.echo(
            f"  {click.style(str(i), bold=True)}. "
            f"{click.style(r['title'], fg='cyan')}  "
            f"{click.style(r['category'], fg='yellow')}  {dist_str}"
        )
        click.echo(f"     {r['roadAddress']}")
        # Enriched rows carry the real 0-5 rating + keywords.
        if "score" in r and r["score"] is not None:
            kws = "  ".join(k["name"] for k in r.get("topKeywords", [])[:4])
            click.echo(f"     {_star(r['score'])}  리뷰 {r['reviewCount']:,}건  ·  ID: {r['id']}")
            if kws:
                click.echo(click.style(f"     🔖 {kws}", fg="bright_black"))
        else:
            click.echo(f"     리뷰 {r['reviewCount']:,}건  ·  ID: {r['id']}")
        click.echo()


# ── detail ────────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("place_id")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON")
def detail(place_id, as_json):
    """Fetch rich details for a place by PLACE_ID."""
    async def _run():
        try:
            cookies = get_session_cookies()
        except Exception as exc:
            _err(str(exc))
        return await fetch_place_detail(place_id, cookies)

    d = asyncio.run(_run())
    result = views.place_detail(d)

    if as_json:
        _json_out(result)
        return

    click.echo()
    click.echo(click.style(result["name"], bold=True, fg="cyan") + f"  [{result['category']}]")
    click.echo(f"  주소   : {result['roadAddress'] or result['address']}")
    click.echo(f"  전화   : {result['phone'] or '-'}")
    click.echo(f"  평점   : {_star(result['score'])}")
    click.echo(f"  방문자 리뷰: {result['visitorReviewTotal']:,}건  블로그 리뷰: {result['blogReviewTotal']:,}건  별점: {result['ratingCount']:,}건")
    if result["topKeywords"]:
        kws = "  ".join(f"{k['name']} ({k['count']})" for k in result["topKeywords"])
        click.echo(f"  키워드 : {kws}")
    click.echo()


# ── reviews ───────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("place_id")
@click.option("--size", default=10, show_default=True, help="Number of reviews to fetch")
@click.option("--after", default=None, help="Pagination cursor from a previous call")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON")
def reviews(place_id, size, after, as_json):
    """Fetch visitor reviews for PLACE_ID."""
    async def _run():
        try:
            cookies = get_session_cookies()
        except Exception as exc:
            _err(str(exc))
        return await get_visitor_reviews(place_id, cookies, size=size, after=after)

    result = views.visitor_reviews(asyncio.run(_run()))

    if as_json:
        _json_out(result)
        return

    click.echo(click.style(f"\n방문자 리뷰  (전체 {result['total']:,}건)\n", bold=True))
    for rv in result["reviews"]:
        author = rv["author"] or "익명"
        rating = "★" * (rv["rating"] or 0) if rv["rating"] else ""
        kws = " · ".join(rv["keywords"]) if rv["keywords"] else ""
        click.echo(click.style(f"  {author}", fg="cyan") + f"  {rating}  {rv['visited'] or ''}")
        if kws:
            click.echo(f"  [{kws}]")
        if rv["body"]:
            body = rv["body"][:200] + ("…" if len(rv["body"]) > 200 else "")
            click.echo(f"  {body}")
        if rv["reply"]:
            click.echo(click.style(f"  └ 사장님: {rv['reply'][:120]}", fg="yellow"))
        click.echo()

    if result["nextCursor"]:
        click.echo(click.style(f"  다음 페이지: --after {result['nextCursor']}", fg="bright_black"))
        click.echo()


# ── review-photos ─────────────────────────────────────────────────────────────

@cli.command("review-photos")
@click.argument("place_id")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON")
def review_photos(place_id, as_json):
    """List review photo URLs and captions for PLACE_ID."""
    async def _run():
        try:
            cookies = get_session_cookies()
        except Exception as exc:
            _err(str(exc))
        return await get_review_photos(place_id, cookies)

    photos = views.review_photos(asyncio.run(_run()))

    if as_json:
        _json_out(photos)
        return

    click.echo(click.style(f"\n리뷰 사진  ({len(photos)}장)\n", bold=True))
    for i, p in enumerate(photos, 1):
        kind = click.style("[동영상]", fg="magenta") if p["isVideo"] else ""
        click.echo(f"  {i}. {kind} {p['url']}")
        if p["text"]:
            click.echo(f"     {p['text'][:100]}")
    click.echo()


# ── theme-lists ───────────────────────────────────────────────────────────────

@cli.command("theme-lists")
@click.argument("place_id")
@click.option("--display", default=3, show_default=True, help="Number of theme lists to return")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON")
def theme_lists(place_id, display, as_json):
    """Fetch curator theme lists that include PLACE_ID."""
    async def _run():
        try:
            cookies = get_session_cookies()
        except Exception as exc:
            _err(str(exc))
        return await get_theme_lists(place_id, cookies, display=display)

    result = views.theme_lists(asyncio.run(_run()))

    if as_json:
        _json_out(result)
        return

    click.echo(click.style(f"\n테마 리스트  (전체 {result['total']}개)\n", bold=True))
    for t in result["lists"]:
        click.echo(click.style(f"  {t['title']}", bold=True) + f"  by {t['author']}  조회 {t['viewCount']:,}  장소 {t['itemCount']}개")
        for rv in t["sampleReviews"]:
            click.echo(f"    • {rv['businessName']}: {rv['body'][:80] if rv['body'] else ''}")
        click.echo()
