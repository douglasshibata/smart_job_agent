import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from smart_job_agent.scraper import Scraper

@pytest.mark.asyncio
async def test_scraper_remote_ok():
    scraper = Scraper()
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value.__aenter__.return_value
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json = MagicMock(return_value=[
            {"legal": "notice"},
            {
                "id": "123",
                "position": "Python Dev",
                "company": "Test Co",
                "location": "Remote",
                "url": "http://test.com",
                "description": "Desc"
            }
        ])
        mock_instance.get.return_value = mock_resp

        jobs = await scraper.get_all_jobs()
        assert len(jobs) == 1
        assert jobs[0]["title"] == "Python Dev"
        assert jobs[0]["external_id"] == "remoteok_123"
