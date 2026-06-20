# naver-places

An MCP server that exposes Naver Maps / Place data (search, place details, visitor reviews, review photos, theme lists) to AI agents.

## Authentication

This server has NO API keys. It authenticates by reusing the cookies of a **Naver account you are already logged into in Google Chrome**. You must:

1. Open Chrome and log in to Naver (https://www.naver.com).
2. Keep that Chrome profile available (Chrome does NOT need to stay open — cookies are read from Chrome's on-disk database; on macOS the decryption key comes from the Keychain).

The server reads cookies automatically; the AI model never sees or manages cookies or tokens. Token/credential lifecycle is entirely server-side.

### Choosing a Chrome profile

By default the server reads the `Default` Chrome profile. To use another profile, set the environment variable:

```
export NAVER_CHROME_PROFILE="Profile 4"
```

Use the `list_available_chrome_profiles` tool to see which profile names exist on the machine.

## Tools

- `search_places(query, coords=None)` — search places by keyword. `coords` is an optional "lat,lng" string that only affects distance ranking; if omitted a default Seoul-center coordinate is used.
- `get_place_detail(place_id)` — name, address, phone, score, review totals, and top review keywords.
- `get_place_visitor_reviews(place_id, size=10, after=None)` — visitor reviews; `after` is a pagination cursor.
- `get_place_images(place_id=None, urls=None, limit=5)` — returns review photos as viewable image content (the model can see them; videos skipped). Image bytes are token-expensive: prefer calling `get_place_review_photos` first for cheap URLs, then pass the URLs you want to view as `urls`. Only Naver CDN URLs are accepted.
- `get_place_review_photos(place_id)` — metadata list of review photos/videos (URLs, captions), no image bytes.
- `get_place_photo_gallery(place_id, cursors=None)` — paginated photo gallery metadata with full dimensions/cursors.
- `get_place_following_reviews(place_id)` — reviews from accounts the logged-in user follows.
- `get_place_theme_lists(place_id, display=3)` — curator theme lists that include the place.
- `list_available_chrome_profiles()` — list Chrome profiles that have a Naver cookie database.

## Running

```
uv run python -m naver_places.server
```

(or wire it into your MCP client config pointing at the `naver_places.server` module).

## Limitations / notes

- Requires being logged into Naver in Chrome on the same machine (macOS Keychain decryption).
- Geocoding is not built in: `search_places` distance ranking uses a fixed default center unless you pass explicit `coords`. (Future enhancement.)
- Some review "photos" are actually videos; image tools skip those.
- The `x-wtm-ncaptcha-token` anti-bot token is currently not required by the endpoints used; if Naver begins enforcing it, requests may need a browser-generated token.
