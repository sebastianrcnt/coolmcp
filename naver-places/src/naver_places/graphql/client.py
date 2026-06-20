import base64
import json
from typing import Any

import httpx
from gql import GraphQLRequest
from graphql import print_ast

PCMAP_GRAPHQL_URL = "https://pcmap-api.place.naver.com/graphql"

_HEADERS = {
    "accept": "*/*",
    "accept-language": "ko",
    "content-type": "application/json",
    "origin": "https://pcmap.place.naver.com",
    "sec-ch-ua": '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/149.0.0.0 Safari/537.36"
    ),
}


def _wtm_header(place_id: str) -> str:
    payload = {"arg": place_id, "type": "place", "source": "place"}
    return base64.b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode()


def _operation_name(request: GraphQLRequest) -> str:
    return request.document.definitions[0].name.value  # type: ignore[attr-defined]


class NaverPlaceGraphQLClient:
    """Thin async client for Naver's pcmap GraphQL endpoint.

    Supports batched requests (array of operations) which the standard
    gql transports do not handle.
    """

    def __init__(self, place_id: str, cookies: dict[str, str]) -> None:
        self.place_id = place_id
        self._cookies = cookies
        self._headers = {
            **_HEADERS,
            "referer": f"https://pcmap.place.naver.com/place/{place_id}/review/visitor",
            "x-wtm-graphql": _wtm_header(place_id),
        }

    async def execute(
        self,
        request: GraphQLRequest,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        results = await self.execute_batch([(request, variables or {})])
        return results[0]

    async def execute_batch(
        self,
        operations: list[tuple[GraphQLRequest, dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        payload = [
            {
                "operationName": _operation_name(request),
                "variables": variables,
                "query": print_ast(request.document),
            }
            for request, variables in operations
        ]
        async with httpx.AsyncClient(
            headers=self._headers, cookies=self._cookies
        ) as client:
            response = await client.post(PCMAP_GRAPHQL_URL, json=payload)
            response.raise_for_status()
            batch = response.json()
            return [item["data"] for item in batch]
