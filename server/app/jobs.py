import json
import logging

from aioredis import Redis
from dotenv import load_dotenv
from httpx import AsyncClient

from app import utils
from app.constants import BASE_URL, TIME_TO_LIVE_IN_CACHE, routes_to_cache

load_dotenv()

logger = logging.getLogger(__name__)


async def refresh_cache(httpx_client: AsyncClient, redis: Redis):
    for key, url in routes_to_cache.items():
        if await redis.get(key):
            logger.info(
                "%s is already in cache, skipping fetching from remote resource",
                key,
            )
            continue
        data = []

        resp = await httpx_client.get(BASE_URL + url)
        if resp.is_success:
            link_header = resp.headers.get("link", None)
            # If the initial request does not have a link header, it is not paginated
            if link_header is None:
                await redis.set(
                    name=key, value=json.dumps(resp.json()), ex=TIME_TO_LIVE_IN_CACHE
                )
                continue

            data.extend(resp.json())
            # Continue to pull the paginated responses based on the Link
            # response header
            while link_header:
                link_obj = utils.parse_link_header(link_header)
                if "next" in link_obj:
                    resp = await httpx_client.get(link_obj["next"])
                    if resp.is_success:
                        data.extend(resp.json())
                        link_header = resp.headers.get("link", None)
                else:
                    break

            logger.info("Caching %s items for the endpoint %s", len(data), key)
            await redis.set(name=key, value=json.dumps(data), ex=TIME_TO_LIVE_IN_CACHE)
