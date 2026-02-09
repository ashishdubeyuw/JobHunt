"""
Web Job Search Module
Search real job listings using free APIs and web scraping
"""

import os
import re
import json
import time
import requests
from typing import List, Dict, Optional
from dataclasses import dataclass
from urllib.parse import quote_plus, urljoin
from bs4 import BeautifulSoup


@dataclass
class JobListing:
    """Standardized job listing format."""
    id: str
    title: str
    company: str
    location: str
    description: str
    salary: str
    apply_url: str
    source: str
    posted_date: str = ""
    required_skills: List[str] = None
    experience_years: int = 0
    
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
            "required_skills": self.required_skills or [],
            "experience_years": self.experience_years
        }


class WebJobSearch:
    """
    Multi-source job search engine.
    
    Supports:
    1. Google Custom Search API (free tier: 100 searches/day)
    2. Serper.dev API (free tier: 2500 searches)
    3. DuckDuckGo (no API needed, basic scraping)
    4. Direct job board scraping (Indeed, LinkedIn - basic)
    """
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # Common skill keywords to extract from descriptions
    SKILL_KEYWORDS = [
        "Python", "Java", "JavaScript", "TypeScript", "C++", "Go", "Rust",
        "React", "Vue", "Angular", "Node.js", "Django", "Flask", "FastAPI",
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform",
        "SQL", "PostgreSQL", "MongoDB", "Redis", "Elasticsearch",
        "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch",
        "NLP", "Computer Vision", "LLM", "RAG", "MLOps",
        "REST API", "GraphQL", "Microservices", "CI/CD", "Git"
    ]
    
    def __init__(
        self,
        google_api_key: Optional[str] = None,
        google_cx: Optional[str] = None,
        serper_api_key: Optional[str] = None,
        rapidapi_key: Optional[str] = None
    ):
        """
        Initialize web job search.
        
        Args:
            google_api_key: Google Custom Search API key
            google_cx: Google Custom Search Engine ID
            serper_api_key: Serper.dev API key
            rapidapi_key: RapidAPI key for JSearch (500 free/month)
        """
        self.google_api_key = google_api_key or os.getenv("GOOGLE_SEARCH_API_KEY")
        self.google_cx = google_cx or os.getenv("GOOGLE_SEARCH_CX")
        self.serper_api_key = serper_api_key or os.getenv("SERPER_API_KEY")
        self.rapidapi_key = rapidapi_key or os.getenv("RAPIDAPI_KEY")
    
    def search_jobs(
        self,
        query: str,
        location: str = "",
        num_results: int = 20,
        source: str = "auto"
    ) -> List[JobListing]:
        """
        Search for jobs across multiple sources.
        
        Args:
            query: Job search query (e.g., "Python Developer")
            location: Location filter (e.g., "Remote", "San Francisco")
            num_results: Number of results to return
            source: Search source ("google_jobs", "jsearch", "serper", "google", "auto")
            
        Returns:
            List of JobListing objects
        """
        jobs = []
        
        if source == "auto":
            # Try sources in order of preference
            # 1. FREE JOB APIs (DEFAULT - Remotive, Arbeitnow, etc. - no API needed, most reliable)
            jobs = self._search_free_apis(query, location, num_results)
            
            # 2. JSearch (RapidAPI) - 500 free/month, real job data (backup)
            if not jobs and self.rapidapi_key:
                jobs = self._search_jsearch(query, location, num_results)
            # 3. Serper.dev - 2500 free searches (backup)
            if not jobs and self.serper_api_key:
                search_query = f'{query} jobs {location} site:linkedin.com/jobs OR site:indeed.com'
                jobs = self._search_serper(search_query, num_results)
        elif source == "free_apis":
            jobs = self._search_free_apis(query, location, num_results)
        elif source == "jsearch":
            jobs = self._search_jsearch(query, location, num_results)
        elif source == "serper":
            search_query = f'{query} jobs {location} site:linkedin.com/jobs OR site:indeed.com'
            jobs = self._search_serper(search_query, num_results)
        
        return jobs[:num_results]
    
    def _search_free_apis(self, query: str, location: str, num_results: int) -> List[JobListing]:
        """Use free job APIs (Remotive, Arbeitnow, etc.) - no API key required."""
        try:
            from .free_job_apis import FreeJobAPIs
            
            api = FreeJobAPIs()
            results = api.search_all(query, location, num_results)
            
            # Convert FreeJobResult to JobListing
            jobs = []
            for result in results:
                job = JobListing(
                    id=result.id,
                    title=result.title,
                    company=result.company,
                    location=result.location,
                    description=result.description,
                    salary=result.salary,
                    apply_url=result.apply_url,
                    source=result.source,
                    posted_date=result.posted_date,
                    required_skills=result.required_skills
                )
                jobs.append(job)
            
            return jobs
        except Exception as e:
            print(f"⚠️ Free APIs error: {e}")
            return []
    
    def _search_google_jobs_scraper(self, query: str, location: str, num_results: int) -> List[JobListing]:
        """Use our custom Google Jobs scraper (no API required)."""
        try:
            from .google_jobs import GoogleJobsScraper
            
            scraper = GoogleJobsScraper()
            results = scraper.search_jobs(query, location, num_results)
            
            # Convert JobResult to JobListing
            jobs = []
            for result in results:
                job = JobListing(
                    id=result.id,
                    title=result.title,
                    company=result.company,
                    location=result.location,
                    description=result.description,
                    salary=result.salary,
                    apply_url=result.apply_url,
                    source=result.source,
                    posted_date=result.posted_date,
                    required_skills=result.required_skills
                )
                jobs.append(job)
            
            return jobs
        except Exception as e:
            print(f"⚠️ Google Jobs scraper error: {e}")
            return []
    
    def _search_jsearch(self, query: str, location: str, num_results: int) -> List[JobListing]:
        """Search using JSearch API from RapidAPI (500 free requests/month)."""
        if not self.rapidapi_key:
            print("⚠️ RapidAPI key not configured")
            return []
        
        jobs = []
        
        try:
            url = "https://jsearch.p.rapidapi.com/search"
            headers = {
                "X-RapidAPI-Key": self.rapidapi_key,
                "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
            }
            params = {
                "query": f"{query} {location}".strip(),
                "page": "1",
                "num_pages": "1"
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            for i, item in enumerate(data.get("data", [])[:num_results]):
                job = JobListing(
                    id=item.get("job_id", f"jsearch_{i}"),
                    title=item.get("job_title", "Unknown Title"),
                    company=item.get("employer_name", "Unknown Company"),
                    location=item.get("job_city", "") + (", " + item.get("job_state", "") if item.get("job_state") else "") or "Remote",
                    description=item.get("job_description", "")[:500],
                    salary=self._format_salary(item.get("job_min_salary"), item.get("job_max_salary")),
                    apply_url=item.get("job_apply_link", "") or item.get("job_google_link", ""),
                    source="jsearch",
                    posted_date=item.get("job_posted_at_datetime_utc", ""),
                    required_skills=item.get("job_required_skills") or self._extract_skills(item.get("job_description", "")),
                    experience_years=item.get("job_required_experience", {}).get("required_experience_in_months", 0) // 12
                )
                jobs.append(job)
            
            print(f"✅ JSearch returned {len(jobs)} jobs")
                    
        except Exception as e:
            print(f"⚠️ JSearch error: {e}")
        
        return jobs
    
    def _format_salary(self, min_sal: Optional[float], max_sal: Optional[float]) -> str:
        """Format salary range."""
        if min_sal and max_sal:
            return f"${int(min_sal):,} - ${int(max_sal):,}"
        elif min_sal:
            return f"${int(min_sal):,}+"
        elif max_sal:
            return f"Up to ${int(max_sal):,}"
        return "Not specified"
    
    def _search_google(self, query: str, num_results: int) -> List[JobListing]:
        """Search using Google Custom Search API."""
        if not self.google_api_key or not self.google_cx:
            print("⚠️ Google API credentials not configured")
            return []
        
        jobs = []
        
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": self.google_api_key,
                "cx": self.google_cx,
                "q": query,
                "num": min(num_results, 10)  # Google max is 10 per request
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            for i, item in enumerate(data.get("items", [])):
                job = self._parse_search_result(item, i, "google")
                if job:
                    jobs.append(job)
                    
        except Exception as e:
            print(f"⚠️ Google search error: {e}")
        
        return jobs
    
    def _search_serper(self, query: str, num_results: int) -> List[JobListing]:
        """Search using Serper.dev API (Google SERP)."""
        if not self.serper_api_key:
            print("⚠️ Serper API key not configured")
            return []
        
        jobs = []
        
        try:
            url = "https://google.serper.dev/search"
            headers = {
                "X-API-KEY": self.serper_api_key,
                "Content-Type": "application/json"
            }
            payload = {
                "q": query,
                "num": min(num_results, 30)
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            for i, item in enumerate(data.get("organic", [])):
                job = self._parse_serper_result(item, i)
                if job:
                    jobs.append(job)
                    
        except Exception as e:
            print(f"⚠️ Serper search error: {e}")
        
        return jobs
    
    def _search_duckduckgo(self, query: str, num_results: int) -> List[JobListing]:
        """Search using DuckDuckGo (no API needed)."""
        jobs = []
        
        try:
            # DuckDuckGo HTML search
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            
            response = requests.get(url, headers=self.HEADERS, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            results = soup.select(".result")
            
            for i, result in enumerate(results[:num_results]):
                job = self._parse_duckduckgo_result(result, i)
                if job:
                    jobs.append(job)
                    
        except Exception as e:
            print(f"⚠️ DuckDuckGo search error: {e}")
        
        return jobs
    
    def _parse_search_result(self, item: Dict, index: int, source: str) -> Optional[JobListing]:
        """Parse Google Custom Search result into JobListing."""
        try:
            title = item.get("title", "")
            link = item.get("link", "")
            snippet = item.get("snippet", "")
            
            # Extract company and job title from result
            parsed = self._extract_job_info(title, snippet, link)
            
            if not parsed["title"]:
                return None
            
            return JobListing(
                id=f"{source}_{index}_{hash(link) % 10000}",
                title=parsed["title"],
                company=parsed["company"],
                location=parsed["location"],
                description=snippet,
                salary=parsed["salary"],
                apply_url=link,
                source=source,
                required_skills=self._extract_skills(snippet)
            )
        except:
            return None
    
    def _parse_serper_result(self, item: Dict, index: int) -> Optional[JobListing]:
        """Parse Serper.dev result into JobListing."""
        try:
            title = item.get("title", "")
            link = item.get("link", "")
            snippet = item.get("snippet", "")
            
            parsed = self._extract_job_info(title, snippet, link)
            
            if not parsed["title"]:
                return None
            
            return JobListing(
                id=f"serper_{index}_{hash(link) % 10000}",
                title=parsed["title"],
                company=parsed["company"],
                location=parsed["location"],
                description=snippet,
                salary=parsed["salary"],
                apply_url=link,
                source="serper",
                required_skills=self._extract_skills(snippet)
            )
        except:
            return None
    
    def _parse_duckduckgo_result(self, result, index: int) -> Optional[JobListing]:
        """Parse DuckDuckGo HTML result into JobListing."""
        try:
            title_elem = result.select_one(".result__title a")
            snippet_elem = result.select_one(".result__snippet")
            
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            link = title_elem.get("href", "")
            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
            
            # Fix DuckDuckGo redirect URLs
            if link.startswith("//duckduckgo.com/l/"):
                # Extract actual URL from redirect
                import urllib.parse
                parsed = urllib.parse.parse_qs(urllib.parse.urlparse(link).query)
                if "uddg" in parsed:
                    link = parsed["uddg"][0]
            
            parsed = self._extract_job_info(title, snippet, link)
            
            if not parsed["title"]:
                return None
            
            return JobListing(
                id=f"ddg_{index}_{hash(link) % 10000}",
                title=parsed["title"],
                company=parsed["company"],
                location=parsed["location"],
                description=snippet,
                salary=parsed["salary"],
                apply_url=link,
                source="duckduckgo",
                required_skills=self._extract_skills(snippet)
            )
        except:
            return None
    
    def _extract_job_info(self, title: str, snippet: str, url: str) -> Dict:
        """Extract structured job info from search result."""
        result = {
            "title": "",
            "company": "",
            "location": "Remote",
            "salary": "Not specified"
        }
        
        # Common patterns in job listing titles
        # "Job Title - Company | LinkedIn"
        # "Job Title at Company - Indeed"
        
        # Clean up title
        title = re.sub(r'\s*\|\s*(LinkedIn|Indeed|Glassdoor).*', '', title)
        title = re.sub(r'\s*-\s*(LinkedIn|Indeed|Glassdoor).*', '', title)
        
        # Try to split "Job Title - Company" or "Job Title at Company"
        if " - " in title:
            parts = title.split(" - ", 1)
            result["title"] = parts[0].strip()
            if len(parts) > 1:
                result["company"] = parts[1].strip()
        elif " at " in title.lower():
            parts = re.split(r'\s+at\s+', title, flags=re.IGNORECASE)
            result["title"] = parts[0].strip()
            if len(parts) > 1:
                result["company"] = parts[1].strip()
        else:
            result["title"] = title
        
        # Extract location from snippet
        location_patterns = [
            r'(Remote|Hybrid|On-site)',
            r'(?:in|at|located in)\s+([A-Z][a-z]+(?:\s*,\s*[A-Z]{2})?)',
            r'([A-Z][a-z]+,\s*[A-Z]{2})',
        ]
        for pattern in location_patterns:
            match = re.search(pattern, snippet, re.IGNORECASE)
            if match:
                result["location"] = match.group(1)
                break
        
        # Extract salary from snippet
        salary_pattern = r'\$[\d,]+(?:\s*-\s*\$[\d,]+)?(?:\s*(?:per|a)\s*(?:year|hour|month))?|[\d,]+k\s*-\s*[\d,]+k'
        match = re.search(salary_pattern, snippet, re.IGNORECASE)
        if match:
            result["salary"] = match.group(0)
        
        return result
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from job description text."""
        found_skills = []
        text_lower = text.lower()
        
        for skill in self.SKILL_KEYWORDS:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        
        return found_skills


class JobBoardScraper:
    """
    Direct scraping of job boards (use responsibly).
    Note: Many job sites have anti-scraping measures.
    """
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    
    def scrape_indeed(self, query: str, location: str = "", num_pages: int = 2) -> List[Dict]:
        """
        Scrape Indeed job listings.
        Note: Indeed has aggressive anti-bot measures. Use with caution.
        """
        jobs = []
        
        for page in range(num_pages):
            try:
                url = f"https://www.indeed.com/jobs?q={quote_plus(query)}&l={quote_plus(location)}&start={page * 10}"
                
                response = requests.get(url, headers=self.HEADERS, timeout=10)
                
                if response.status_code != 200:
                    print(f"⚠️ Indeed returned status {response.status_code}")
                    break
                
                soup = BeautifulSoup(response.text, "html.parser")
                job_cards = soup.select('[data-testid="job-card"]') or soup.select(".job_seen_beacon")
                
                for card in job_cards:
                    job = self._parse_indeed_card(card)
                    if job:
                        jobs.append(job)
                
                time.sleep(2)  # Rate limiting
                
            except Exception as e:
                print(f"⚠️ Indeed scraping error: {e}")
                break
        
        return jobs
    
    def _parse_indeed_card(self, card) -> Optional[Dict]:
        """Parse Indeed job card HTML."""
        try:
            title_elem = card.select_one("h2 a") or card.select_one(".jobTitle a")
            company_elem = card.select_one('[data-testid="company-name"]') or card.select_one(".companyName")
            location_elem = card.select_one('[data-testid="text-location"]') or card.select_one(".companyLocation")
            
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            job_key = title_elem.get("data-jk") or ""
            
            return {
                "id": f"indeed_{job_key}",
                "title": title,
                "company": company_elem.get_text(strip=True) if company_elem else "Unknown",
                "location": location_elem.get_text(strip=True) if location_elem else "Unknown",
                "description": "",
                "salary": "Not specified",
                "apply_url": f"https://www.indeed.com/viewjob?jk={job_key}" if job_key else "",
                "source": "indeed",
                "required_skills": [],
                "experience_years": 0
            }
        except:
            return None


def search_web_jobs(
    query: str,
    location: str = "",
    num_results: int = 20,
    serper_api_key: Optional[str] = None
) -> List[Dict]:
    """
    Convenience function to search for jobs on the web.
    
    Args:
        query: Job search query
        location: Location filter
        num_results: Number of results
        serper_api_key: Optional Serper.dev API key
        
    Returns:
        List of job dictionaries
    """
    searcher = WebJobSearch(serper_api_key=serper_api_key)
    jobs = searcher.search_jobs(query, location, num_results)
    return [j.to_dict() for j in jobs]
