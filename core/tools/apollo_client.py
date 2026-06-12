"""Apollo.io enrichment — busca emails via people/search."""
from __future__ import annotations

import asyncio
import httpx
from core.logger import get_logger

logger = get_logger("core.tools.apollo_client")

_PEOPLE_SEARCH_URL = "https://api.apollo.io/api/v1/mixed_people/search"


async def _search_one(client: httpx.AsyncClient, candidate: dict, api_key: str) -> str | None:
    name = candidate.get("name", "")
    company = candidate.get("company", "")
    linkedin_url = candidate.get("source_url", "")

    body: dict = {
        "api_key": api_key,
        "q_person_name": name,
        "per_page": 1,
        "page": 1,
    }
    if company and company not in ("Por confirmar", "Unknown", ""):
        body["organization_name"] = company
    if "linkedin.com/in/" in linkedin_url:
        body["person_linkedin_url"] = linkedin_url

    try:
        resp = await client.post(_PEOPLE_SEARCH_URL, json=body)
        resp.raise_for_status()
        data = resp.json()
        people = data.get("people", [])
        if people:
            email = people[0].get("email", "")
            if email and "@" in email:
                logger.info("[APOLLO] Found email for %s", name)
                return email
    except Exception as exc:
        logger.error("[APOLLO] Error searching %s: %s", name, exc)
    return None


async def enrich_emails(
    candidates: list[dict],
    api_key: str,
    reveal_personal: bool = False,
) -> dict[str, str]:
    """Return {dedup_key: email} for candidates Apollo found.
    Each candidate dict must have: dedup_key, name, company, source_url.
    """
    if not api_key or not candidates:
        return {}

    results: dict[str, str] = {}
    # Throttle to 3 concurrent requests to avoid rate limits
    semaphore = asyncio.Semaphore(3)

    async def fetch(c: dict) -> None:
        async with semaphore:
            async with httpx.AsyncClient(timeout=15) as client:
                email = await _search_one(client, c, api_key)
                if email:
                    results[c["dedup_key"]] = email

    await asyncio.gather(*[fetch(c) for c in candidates])
    return results
