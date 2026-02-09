"""
Google Jobs Scraper
Custom job search engine using Google Jobs search results.
No API key required - extracts job listings from public Google search pages.
"""

import os
import re
import json
import time
import random
import requests
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from urllib.parse import quote_plus, urlencode
from bs4 import BeautifulSoup


@dataclass
class JobResult:
    """Standardized job result."""
    id: str
    title: str
    company: str
    location: str
    description: str
    salary: str
    apply_url: str
    source: str
    posted_date: str = ""
    job_type: str = ""
    required_skills: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "description": self.description,
            "salary": self.salary,
            "apply_url": self.apply_url,
            "source": self.source,
            "posted_date": self.posted_date,
            "job_type": self.job_type,
            "required_skills": self.required_skills,
            "experience_years": 0
        }


class GoogleJobsScraper:
    """
    Scrape job listings from Google Jobs search.
    
    Uses Google's public search with special parameters to get job results.
    No API key required.
    """
    
    # Rotate user agents to avoid blocks
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]
    
    # Common skills to extract
    SKILL_KEYWORDS = [
        "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust", "Ruby", "PHP",
        "React", "Vue", "Angular", "Node.js", "Django", "Flask", "FastAPI", "Spring",
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform", "Jenkins", "CI/CD",
        "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "GraphQL",
        "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "NLP", "Computer Vision",
        "REST API", "Microservices", "Git", "Linux", "Agile", "Scrum"
    ]
    
    def __init__(self, delay_range: Tuple[float, float] = (1.0, 3.0)):
        """
        Initialize the Google Jobs scraper.
        
        Args:
            delay_range: Min/max delay between requests to avoid rate limiting
        """
        self.delay_range = delay_range
        self.session = requests.Session()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get randomized headers."""
        return {
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }
    
    def search_jobs(
        self,
        query: str,
        location: str = "",
        num_results: int = 20
    ) -> List[JobResult]:
        """
        Search for jobs using Google.
        
        Args:
            query: Job search query (e.g., "Python Developer")
            location: Location filter (e.g., "Remote", "New York")
            num_results: Number of results to return
            
        Returns:
            List of JobResult objects
        """
        jobs = []
        
        # Try multiple search strategies
        strategies = [
            self._search_google_jobs_direct,
            self._search_google_organic,
            self._search_via_startpage,
        ]
        
        for strategy in strategies:
            try:
                results = strategy(query, location, num_results)
                if results:
                    jobs.extend(results)
                    print(f"✅ Found {len(results)} jobs using {strategy.__name__}")
                    break
            except Exception as e:
                print(f"⚠️ {strategy.__name__} failed: {e}")
                continue
        
        # Remove duplicates based on title + company
        seen = set()
        unique_jobs = []
        for job in jobs:
            key = f"{job.title}|{job.company}".lower()
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        return unique_jobs[:num_results]
    
    def _search_google_jobs_direct(
        self,
        query: str,
        location: str,
        num_results: int
    ) -> List[JobResult]:
        """Search Google Jobs directly."""
        jobs = []
        
        # Build Google Jobs search URL
        search_term = f"{query} jobs {location}".strip()
        params = {
            "q": search_term,
            "ibp": "htl;jobs",  # Google Jobs trigger
            "hl": "en",
            "gl": "us"
        }
        url = f"https://www.google.com/search?{urlencode(params)}"
        
        # Add delay
        time.sleep(random.uniform(*self.delay_range))
        
        response = self.session.get(url, headers=self._get_headers(), timeout=15)
        
        if response.status_code != 200:
            print(f"⚠️ Google returned status {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Try to find job listings in Google Jobs format
        # Google Jobs uses various div structures
        job_cards = soup.select('div[data-ved]') or soup.select('.iFjolb') or soup.select('li.iFjolb')
        
        for i, card in enumerate(job_cards[:num_results]):
            job = self._parse_google_job_card(card, i)
            if job:
                jobs.append(job)
        
        return jobs
    
    def _search_google_organic(
        self,
        query: str,
        location: str,
        num_results: int
    ) -> List[JobResult]:
        """Search Google organic results for job listings."""
        jobs = []
        
        # Search for job board results
        search_term = f"{query} jobs {location} site:linkedin.com/jobs OR site:indeed.com OR site:glassdoor.com"
        params = {
            "q": search_term,
            "num": min(num_results, 20),
            "hl": "en"
        }
        url = f"https://www.google.com/search?{urlencode(params)}"
        
        time.sleep(random.uniform(*self.delay_range))
        
        response = self.session.get(url, headers=self._get_headers(), timeout=15)
        
        if response.status_code != 200:
            return []
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find organic search results
        results = soup.select('div.g') or soup.select('div[data-sokoban-container]')
        
        for i, result in enumerate(results[:num_results]):
            job = self._parse_organic_result(result, i)
            if job:
                jobs.append(job)
        
        return jobs
    
    def _search_via_startpage(
        self,
        query: str,
        location: str,
        num_results: int
    ) -> List[JobResult]:
        """Use Startpage (privacy-focused Google proxy) as fallback."""
        jobs = []
        
        search_term = f"{query} jobs {location} site:linkedin.com/jobs OR site:indeed.com"
        url = f"https://www.startpage.com/sp/search?q={quote_plus(search_term)}"
        
        time.sleep(random.uniform(*self.delay_range))
        
        response = self.session.get(url, headers=self._get_headers(), timeout=15)
        
        if response.status_code != 200:
            return []
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Startpage result structure
        results = soup.select('.w-gl__result') or soup.select('.result')
        
        for i, result in enumerate(results[:num_results]):
            job = self._parse_startpage_result(result, i)
            if job:
                jobs.append(job)
        
        return jobs
    
    def _parse_google_job_card(self, card, index: int) -> Optional[JobResult]:
        """Parse a Google Jobs card."""
        try:
            # Try various selectors for job title
            title_elem = (
                card.select_one('.BjJfJf') or 
                card.select_one('.PUpOsf') or 
                card.select_one('h3') or
                card.select_one('[role="heading"]')
            )
            
            # Company name
            company_elem = (
                card.select_one('.vNEEBe') or 
                card.select_one('.nJlQNd') or
                card.select_one('.company')
            )
            
            # Location
            location_elem = (
                card.select_one('.Qk80Jf') or 
                card.select_one('.location')
            )
            
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            company = company_elem.get_text(strip=True) if company_elem else "Unknown Company"
            location = location_elem.get_text(strip=True) if location_elem else "Remote"
            
            # Clean up title
            title = re.sub(r'\s*-\s*(LinkedIn|Indeed|Glassdoor).*', '', title)
            
            # Get link
            link_elem = card.select_one('a[href]')
            apply_url = link_elem.get('href', '') if link_elem else ''
            
            # Clean Google redirect URLs
            if apply_url.startswith('/url?'):
                match = re.search(r'q=([^&]+)', apply_url)
                if match:
                    apply_url = requests.utils.unquote(match.group(1))
            
            # Extract description
            desc_elem = card.select_one('.HBvzbc') or card.select_one('.description')
            description = desc_elem.get_text(strip=True)[:500] if desc_elem else ""
            
            return JobResult(
                id=f"google_{index}_{hash(title + company) % 10000}",
                title=title,
                company=company,
                location=location,
                description=description,
                salary=self._extract_salary(card.get_text()),
                apply_url=apply_url or f"https://www.google.com/search?q={quote_plus(title + ' ' + company + ' jobs')}",
                source="google_jobs",
                required_skills=self._extract_skills(description)
            )
        except Exception as e:
            return None
    
    def _parse_organic_result(self, result, index: int) -> Optional[JobResult]:
        """Parse a Google organic search result."""
        try:
            # Title
            title_elem = result.select_one('h3')
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            
            # Link
            link_elem = result.select_one('a[href]')
            apply_url = link_elem.get('href', '') if link_elem else ''
            
            # Skip non-job URLs
            job_sites = ['linkedin.com/jobs', 'indeed.com', 'glassdoor.com', 'ziprecruiter.com']
            if not any(site in apply_url.lower() for site in job_sites):
                return None
            
            # Snippet/description
            snippet_elem = result.select_one('.VwiC3b') or result.select_one('.st')
            description = snippet_elem.get_text(strip=True) if snippet_elem else ""
            
            # Parse title for job info
            parsed = self._parse_job_title(title)
            
            return JobResult(
                id=f"organic_{index}_{hash(apply_url) % 10000}",
                title=parsed["title"],
                company=parsed["company"],
                location=self._extract_location(description) or "Remote",
                description=description,
                salary=self._extract_salary(description),
                apply_url=apply_url,
                source="google_organic",
                required_skills=self._extract_skills(description)
            )
        except:
            return None
    
    def _parse_startpage_result(self, result, index: int) -> Optional[JobResult]:
        """Parse a Startpage search result."""
        try:
            title_elem = result.select_one('h3') or result.select_one('.w-gl__result-title')
            link_elem = result.select_one('a.w-gl__result-url') or result.select_one('a[href]')
            snippet_elem = result.select_one('.w-gl__description') or result.select_one('p')
            
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            apply_url = link_elem.get('href', '') if link_elem else ''
            description = snippet_elem.get_text(strip=True) if snippet_elem else ""
            
            # Skip non-job URLs
            job_sites = ['linkedin.com/jobs', 'indeed.com', 'glassdoor.com']
            if not any(site in apply_url.lower() for site in job_sites):
                return None
            
            parsed = self._parse_job_title(title)
            
            return JobResult(
                id=f"startpage_{index}_{hash(apply_url) % 10000}",
                title=parsed["title"],
                company=parsed["company"],
                location=self._extract_location(description) or "Remote",
                description=description,
                salary=self._extract_salary(description),
                apply_url=apply_url,
                source="startpage",
                required_skills=self._extract_skills(description)
            )
        except:
            return None
    
    def _parse_job_title(self, title: str) -> Dict[str, str]:
        """Parse job title to extract job name and company."""
        result = {"title": title, "company": "Unknown Company"}
        
        # Clean common suffixes
        title = re.sub(r'\s*\|\s*(LinkedIn|Indeed|Glassdoor).*', '', title)
        title = re.sub(r'\s*-\s*(LinkedIn|Indeed|Glassdoor).*', '', title)
        
        # Try "Job Title - Company" pattern
        if " - " in title:
            parts = title.split(" - ", 1)
            result["title"] = parts[0].strip()
            if len(parts) > 1:
                result["company"] = parts[1].strip()
        # Try "Job Title at Company" pattern
        elif " at " in title.lower():
            parts = re.split(r'\s+at\s+', title, flags=re.IGNORECASE)
            result["title"] = parts[0].strip()
            if len(parts) > 1:
                result["company"] = parts[1].strip()
        
        return result
    
    def _extract_salary(self, text: str) -> str:
        """Extract salary from text."""
        patterns = [
            r'\$[\d,]+(?:\s*-\s*\$[\d,]+)?(?:\s*(?:per|a|/)\s*(?:year|yr|hour|hr|month))?',
            r'[\d,]+k\s*-\s*[\d,]+k',
            r'USD\s*[\d,]+(?:\s*-\s*[\d,]+)?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return "Not specified"
    
    def _extract_location(self, text: str) -> Optional[str]:
        """Extract location from text."""
        patterns = [
            r'(Remote|Hybrid|On-site|Onsite)',
            r'(?:in|at|located in)\s+([A-Z][a-z]+(?:\s*,\s*[A-Z]{2})?)',
            r'([A-Z][a-z]+,\s*[A-Z]{2})',
            r'(New York|San Francisco|Los Angeles|Seattle|Austin|Denver|Chicago|Boston|Miami)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from job description."""
        found_skills = []
        text_lower = text.lower()
        
        for skill in self.SKILL_KEYWORDS:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        
        return found_skills[:10]  # Limit to top 10


def search_google_jobs(
    query: str,
    location: str = "",
    num_results: int = 20
) -> List[Dict]:
    """
    Convenience function to search Google Jobs.
    
    Args:
        query: Job search query
        location: Location filter
        num_results: Number of results
        
    Returns:
        List of job dictionaries
    """
    scraper = GoogleJobsScraper()
    jobs = scraper.search_jobs(query, location, num_results)
    return [j.to_dict() for j in jobs]
