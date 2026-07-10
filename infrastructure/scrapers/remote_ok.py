import httpx
import logging
from typing import List, Dict, Any
from ...domain.interfaces import JobScraper

logger = logging.getLogger(__name__)

class RemoteOkScraper(JobScraper):
    async def fetch_remote_ok_jobs(self) -> List[Dict[str, Any]]:
        url = "https://remoteok.com/api"
        # RemoteOK API is a bit peculiar, the first element is a legal notice usually
        async with httpx.AsyncClient() as client:
            try:
                # Add user agent to avoid being blocked
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, list) and len(data) > 1:
                    return data[1:] # Skip legal notice
                return []
            except Exception as e:
                logger.error(f"Error fetching from RemoteOK: {e}")
                return []

    async def get_all_jobs(self) -> List[Dict[str, Any]]:
        remote_ok = await self.fetch_remote_ok_jobs()
        # Transform RemoteOK format to our internal format
        normalized = []
        for j in remote_ok:
            normalized.append({
                "external_id": f"remoteok_{j.get('id')}",
                "title": j.get("position"),
                "company": j.get("company"),
                "location": j.get("location"),
                "salary": f"{j.get('salary_min')} - {j.get('salary_max')}" if j.get('salary_min') else "Not specified",
                "link": j.get("url"),
                "description": j.get("description")
            })
        return normalized
