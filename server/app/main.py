import logging
import os
from contextlib import asynccontextmanager
from typing import Literal

import aioredis
import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dotenv import load_dotenv
from fastapi import FastAPI, Response

from app import jobs
from app.constants import BASE_URL, REFRESH_JOB_INTERVAL
from app.controllers import create_view, retrieve_from_cache

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if os.getenv("GITHUB_API_TOKEN") is None:
    logger.error(
        "Could not find GITHUB_API_TOKEN in environment! Please pass as environment variable!"
    )
redis = aioredis.from_url("redis://redis:6379")
httpx_client = httpx.AsyncClient(
    headers={"Authorization": f"Bearer {os.getenv('GITHUB_API_TOKEN')}"}
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        jobs.refresh_cache,
        IntervalTrigger(seconds=REFRESH_JOB_INTERVAL),
        args=[httpx_client, redis],
    )
    scheduler.start()
    await jobs.refresh_cache(httpx_client=httpx_client, redis=redis)

    yield

    scheduler.shutdown()
    await redis.close()
    await httpx_client.aclose()


fastapi_app = FastAPI(lifespan=lifespan)


@fastapi_app.get("/")
async def root():
    return await retrieve_from_cache(key="BASE", redis=redis, httpx_client=httpx_client)


@fastapi_app.get("/orgs/Netflix")
async def org():
    return await retrieve_from_cache(key="ORGS", redis=redis, httpx_client=httpx_client)


@fastapi_app.get("/orgs/Netflix/members")
async def org_members():
    return await retrieve_from_cache(
        key="ORG_MEMBERS", redis=redis, httpx_client=httpx_client
    )


@fastapi_app.get("/orgs/Netflix/repos")
async def org_repos():
    return await retrieve_from_cache(
        key="ORG_REPOS", redis=redis, httpx_client=httpx_client
    )


@fastapi_app.get("/view/bottom/{n}/{sort_field}")
async def get_vew(
    n: int,
    sort_field: Literal[
        "forks",
        "last_updated",
        "open_issues",
        "stars",
    ],
):
    org_data = await retrieve_from_cache(
        key="ORG_REPOS", redis=redis, httpx_client=httpx_client
    )

    return await create_view(n=n, sort_field=sort_field, org_data=org_data)


@fastapi_app.get("/healthcheck")
async def healthcheck():
    try:
        redis_ping = await redis.ping()
        if redis_ping:
            return {"status": "ok"}
    except Exception as e:  # pylint: disable=broad-except
        logger.error("Healthcheck failed: %s", e)
        return {"status": "error", "details": str(e)}


@fastapi_app.post("/clear-cache")
async def clear_cache():
    await redis.flushall()


@fastapi_app.get("/cached-keys")
async def list_cached_keys():
    return await redis.keys()


@fastapi_app.get("/{full_path:path}")
async def proxy_to_github(response: Response, full_path: str):
    if full_path[0] != "/":
        full_path = "/" + full_path

    resp = await httpx_client.get(BASE_URL + full_path)

    # Include additional headers that you would like to have proxied through
    # the service; currently only passing the link header if exists to allow
    # clients to paginate their responses for endpoints outside of the cached ones
    include_headers = {"link"}
    for header, value in resp.headers.items():
        if header.lower() in include_headers:
            response.headers[header] = value
    if resp.is_success:
        return resp.json()
    return resp.content
