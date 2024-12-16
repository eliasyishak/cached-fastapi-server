import json
import logging
from datetime import datetime
from typing import Literal, Optional

from aioredis import Redis
from httpx import AsyncClient

from app.jobs import refresh_cache

logger = logging.getLogger(__name__)

SupportedCacheKeys = Literal[
    "BASE",
    "ORGS",
    "ORG_MEMBERS",
    "ORG_REPOS",
]


async def retrieve_from_cache(
    key: SupportedCacheKeys, redis: Redis, httpx_client: AsyncClient
) -> Optional[dict]:
    cached_value = await redis.get(key)
    if cached_value:
        logger.info("Pulling %s data from redis cache...", key)
        return json.loads(cached_value)

    await refresh_cache(httpx_client=httpx_client, redis=redis)
    return json.loads(await redis.get(key))


async def create_view(
    n: int,
    sort_field: Literal[
        "forks",
        "last_updated",
        "open_issues",
        "stars",
    ],
    org_data: list,
):
    key_lookup = {
        "forks": "forks",
        "last_updated": "updated_at",
        "open_issues": "open_issues",
        "stars": "stargazers_count",
    }
    if sort_field == "last_updated":
        org_data.sort(
            key=lambda item: (
                -datetime.strptime(
                    item[key_lookup[sort_field]], "%Y-%m-%dT%H:%M:%SZ"
                ).timestamp(),
                item["full_name"],
            ),
            reverse=False,
        )
    else:
        org_data.sort(
            key=lambda item: (
                (-item[key_lookup[sort_field]], item["full_name"]),
                item["full_name"],
            ),
            reverse=False,
        )

    return list(
        map(
            lambda item: [item["full_name"], item[key_lookup[sort_field]]],
            org_data[-n:],
        )
    )
