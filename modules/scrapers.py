"""
Job Scraper Module
Fetches job listings from APIs or uses mock data for development
"""

import json
import os
import requests
from typing import List, Dict, Optional
from pathlib import Path


class JobScraper:
    """
    Job scraper with ScrapingDog API support and mock data fallback.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("SCRAPINGDOG_API_KEY")
        self.base_url = "https://api.scrapingdog.com/scrape"
    
    def scrape_jobs(self, query: str, location: str = "", num_results: int = 10) -> List[Dict]:
        """
        Scrape job listings from job boards.
        Falls back to mock data if API key is not set.
        
        Args:
            query: Job search query (e.g., "Software Engineer")
            location: Location filter (e.g., "San Francisco, CA")
            num_results: Number of results to return
            
        Returns:
            List of job dictionaries
        """
        if not self.api_key:
            print("⚠️ No ScrapingDog API key found. Using mock data.")
            return self._filter_mock_jobs(query, location, num_results)
        
        try:
            jobs = self._scrape_with_api(query, location, num_results)
            return jobs
        except Exception as e:
            print(f"⚠️ Scraping failed: {e}. Using mock data.")
            return self._filter_mock_jobs(query, location, num_results)
    
    def _scrape_with_api(self, query: str, location: str, num_results: int) -> List[Dict]:
        """
        Scrape jobs using ScrapingDog API.
        This is a placeholder - actual implementation depends on target job board.
        """
        # Example: Scraping LinkedIn Jobs (would need proper URL construction)
        target_url = f"https://www.linkedin.com/jobs/search?keywords={query}&location={location}"
        
        params = {
            "api_key": self.api_key,
            "url": target_url,
            "dynamic": "false"
        }
        
        response = requests.get(self.base_url, params=params, timeout=30)
        response.raise_for_status()
        
        # Parse HTML response (simplified - would need BeautifulSoup parsing)
        # For now, return mock data as placeholder
        return self._filter_mock_jobs(query, location, num_results)
    
    def _filter_mock_jobs(self, query: str, location: str, num_results: int) -> List[Dict]:
        """Filter mock jobs based on query and location."""
        jobs = load_mock_jobs()
        
        filtered = []
        query_lower = query.lower()
        location_lower = location.lower()
        
        for job in jobs:
            title_match = query_lower in job.get("title", "").lower()
            desc_match = query_lower in job.get("description", "").lower()
            skills_match = any(query_lower in skill.lower() for skill in job.get("required_skills", []))
            
            if title_match or desc_match or skills_match:
                if not location or location_lower in job.get("location", "").lower():
                    filtered.append(job)
        
        # If no matches, return all jobs
        if not filtered:
            filtered = jobs
        
        return filtered[:num_results]


def load_mock_jobs() -> List[Dict]:
    """
    Load mock job data from JSON file.
    
    Returns:
        List of job dictionaries
    """
    mock_file = Path(__file__).parent.parent / "data" / "mock_jobs.json"
    
    try:
        with open(mock_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️ Mock data file not found at {mock_file}")
        return get_default_mock_jobs()
    except json.JSONDecodeError as e:
        print(f"⚠️ Error parsing mock data: {e}")
        return get_default_mock_jobs()


def get_default_mock_jobs() -> List[Dict]:
    """Return minimal default job data if file is missing."""
    return [
        {
            "id": "default_001",
            "title": "Software Engineer",
            "company": "Demo Company",
            "location": "Remote",
            "salary": "$100,000 - $150,000",
            "description": "Full-stack development role. Python, JavaScript, React, AWS experience required.",
            "apply_url": "https://example.com/apply",
            "required_skills": ["Python", "JavaScript", "React", "AWS"],
            "experience_years": 3,
            "posted_date": "2026-02-01"
        },
        {
            "id": "default_002",
            "title": "Data Scientist",
            "company": "Demo Analytics",
            "location": "Remote",
            "salary": "$120,000 - $160,000",
            "description": "Build ML models and analyze data. Python, SQL, Machine Learning required.",
            "apply_url": "https://example.com/apply-ds",
            "required_skills": ["Python", "SQL", "Machine Learning", "TensorFlow"],
            "experience_years": 2,
            "posted_date": "2026-02-01"
        }
    ]
