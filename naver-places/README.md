# naver-places

An MCP server that exposes Naver Maps / Place data (search, place details, visitor reviews, review photos, theme lists) to AI agents.

## Authentication

This server has NO API keys. Authentication via Chrome cookies is now **optional**.

Public features (search, place detail, visitor reviews, photos) work completely anonymously — no login required and no Chrome cookies needed. If Chrome cookies can't be read (e.g. a locked Linux GNOME keyring), the server automatically falls back to an anonymous Naver session. Only personalized features (following reviews) require a logged-in Chrome account.

To enable anonymous fallback (default), simply run the server. To disable the fallback and require a real login:

```
export NAVER_ALLOW_ANONYMOUS=0
```

Alternatively, supply cookies directly as a JSON object without reading Chrome:

```
export NAVER_COOKIES='{"cookie_name": "value", ...}'
```

If you do log in, the server reuses the cookies of a **Naver account you are already logged into in Google Chrome**. Simply:

1. Open Chrome and log in to Naver (https://www.naver.com).
2. Keep that Chrome profile available (Chrome does NOT need to stay open — cookies are read from Chrome's on-disk database; on macOS the decryption key comes from the Keychain, on Linux from `~/.config/google-chrome`).

The server reads cookies automatically; the AI model never sees or manages cookies or tokens. Token/credential lifecycle is entirely server-side.

### Choosing a Chrome profile

By default the server reads the `Default` Chrome profile. To use another profile, set the environment variable:

```
export NAVER_CHROME_PROFILE="Profile 4"
```

Use the `list_available_chrome_profiles` tool to see which profile names exist on the machine.

## Tools

- `search_places(query, coords=None, near=None, enrich=False, top=3)` — search places by keyword. Returns a dict `{ "searchedNear": {...}, "places": [...] }`. `searchedNear` reports the ranking center used (including `resolvedTo` for geocoded landmarks and `source`: "coords" | "near" | "default"), so you can confirm where the search centered. `query` should be a short keyword (dish or business name), not a sentence with a location in it — use `near` instead. `near` is a landmark name (e.g. "성균관대") that gets auto-geocoded to coordinates for distance ranking. `coords` is an alternative "lat,lng" string for explicit coordinates; if both are omitted a default Seoul-center coordinate is used. Note: search returns `rankingScore` (Naver's internal relevance weight, NOT a 0-5 rating); the real 0-5 rating comes from `get_place_detail` (`score`). When `enrich=True`, the top `top` results also include the real 0-5 `score`, `visitorReviewTotal`, `phone`, and `topKeywords` — fetched in one call instead of calling `get_place_detail` per candidate (saves round trips). `score` is null if a place's detail couldn't be fetched.
- `get_place_detail(place_id)` — name, address, phone, score, review totals, and top review keywords.
- `get_place_visitor_reviews(place_id, size=10, after=None)` — visitor reviews; `after` is a pagination cursor.
- `get_place_images(place_id=None, urls=None, limit=5)` — returns review photos as viewable image content (the model can see them; videos skipped). Image bytes are token-expensive: prefer calling `get_place_review_photos` first for cheap URLs, then pass the URLs you want to view as `urls`. Only Naver CDN URLs are accepted.
- `get_place_review_photos(place_id)` — metadata list of review photos/videos (URLs, captions), no image bytes.
- `get_place_photo_gallery(place_id, cursors=None)` — paginated photo gallery metadata with full dimensions/cursors.
- `get_place_following_reviews(place_id)` — reviews from accounts the logged-in user follows.
- `get_place_theme_lists(place_id, display=3)` — curator theme lists that include the place.
- `list_available_chrome_profiles()` — list Chrome profiles that have a Naver cookie database.

## CLI

A CLI is available alongside the MCP server. Run commands with:

```
uv run --package naver-places naver-places <cmd>
```

Commands:

- `search QUERY [--near LANDMARK] [--coords LAT,LNG] [--enrich] [--top N] [--json]` — search places. Use a short keyword for QUERY (dish/business name); put location in --near (e.g. `search "순두부찌개" --near "성균관대"`), NOT in QUERY. Use `--enrich` to attach rating, review count, phone, and keywords to the top results in one call (e.g. `search "순두부찌개" --near "성균관대" --enrich`).
- `detail PLACE_ID [--json]` — place details.
- `reviews PLACE_ID [--size N] [--after CURSOR] [--json]` — visitor reviews.
- `review-photos PLACE_ID [--json]` — review photo metadata.
- `theme-lists PLACE_ID [--display N] [--json]` — theme lists containing this place.
- `auth [--profile NAME]` — show login/anonymous mode status.
- `profiles` — list available Chrome profiles.

## Running

Run the MCP server with:

```
uv run python -m naver_places.server
```

Alternatively, use the console script entry point:

```
naver-places-mcp
```

### Registering with an MCP client

Add the following to your MCP client's configuration (e.g., Claude Code or cline):

```json
{
  "mcpServers": {
    "naver-places": {
      "command": "uv",
      "args": ["run", "--package", "naver-places", "naver-places-mcp"]
    }
  }
}
```

Or register directly with Claude Code in one line:

```
claude mcp add naver-places -- uv run --package naver-places naver-places-mcp
```

## Limitations / notes

- Chrome login is now optional; public features work anonymously. If you do log in, Chrome must be on the same machine (macOS Keychain or Linux `~/.config/google-chrome` for decryption).
- Responses (search results and place details) are cached in-process for a short time (default 120s) to reduce latency and avoid Naver rate-limiting (HTTP 429). Disable with `NAVER_CACHE=0` or configure duration with `NAVER_CACHE_TTL=<seconds>`.
- Geocoding is available via the `near` parameter: it resolves a landmark name to the top matching place's coordinates.
- Some review "photos" are actually videos; image tools skip those.
- The `x-wtm-ncaptcha-token` anti-bot token is currently not required by the endpoints used; if Naver begins enforcing it, requests may need a browser-generated token.
