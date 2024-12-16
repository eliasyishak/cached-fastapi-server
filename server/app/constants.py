BASE_URL = "https://api.github.com"

# TTL in seconds; how long the key should remain in cache
TIME_TO_LIVE_IN_CACHE = 60 * 60

# How often the job should be run in seconds
REFRESH_JOB_INTERVAL = 60 * 30

# The pattern to match on for parsing the link response header
LINK_HEADER_PATTERN = r'<(?P<link>[^>]+)>;\s*rel="(?P<rel>[^"]+)"'

# The routes we will cache on a periodic timer
routes_to_cache = {
    "BASE": "/",
    "ORGS": "/orgs/Netflix",
    "ORG_MEMBERS": "/orgs/Netflix/members",
    "ORG_REPOS": "/orgs/Netflix/repos",
}
