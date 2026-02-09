"""
Free Job APIs Module
Uses completely free job APIs that don't require any API keys.
"""

import os
import re
import json
import time
import requests
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class FreeJobResult:
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


class FreeJobAPIs:
    """
    Collection of completely free job APIs that don't require API keys.
    
    Sources:
    1. Remotive.io - Remote tech jobs
    2. Arbeitnow - European + Remote jobs  
    3. Findwork.dev - Developer jobs
    4. Himalayas - Remote jobs
    """
    
    DEFAULT_SKILL_KEYWORDS = [
        "Python", "Java", "JavaScript", "TypeScript", "C++", "Go", "Rust", "Ruby",
        "React", "Vue", "Angular", "Node.js", "Django", "Flask", "FastAPI",
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform",
        "SQL", "PostgreSQL", "MongoDB", "Redis", "Machine Learning", "AI",
        "Deep Learning", "TensorFlow", "PyTorch", "NLP", "Computer Vision"
    ]
    
    def __init__(self, resume_skills: List[str] = None):
        """
        Initialize with optional resume skills.
        
        Args:
            resume_skills: Skills extracted from user's resume. If provided,
                          these are used as the primary skill keywords for matching.
        """
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "JobMatchingApp/1.0",
            "Accept": "application/json"
        })
        # Use resume skills first, then fall back to defaults
        if resume_skills and len(resume_skills) > 0:
            # Combine resume skills with defaults (resume skills first)
            self.skill_keywords = list(resume_skills) + [
                s for s in self.DEFAULT_SKILL_KEYWORDS 
                if s.lower() not in [rs.lower() for rs in resume_skills]
            ]
            print(f"🎯 Using resume skills for matching: {', '.join(resume_skills[:10])}")
        else:
            self.skill_keywords = self.DEFAULT_SKILL_KEYWORDS
    
    def search_all(self, query: str, location: str = "", num_results: int = 20) -> List[FreeJobResult]:
        """Search all free job APIs and combine results."""
        all_jobs = []
        
        # Extract individual keywords from query for matching
        self.query_keywords = [w.strip().lower() for w in re.split(r'[,\s]+', query) 
                               if len(w.strip()) > 2 and w.strip().lower() not in ('jobs', 'remote', 'and', 'the', 'for')]
        print(f"🔍 Search keywords: {self.query_keywords}")
        
        # Try each API
        apis = [
            ("Remotive", self._search_remotive),
            ("Arbeitnow", self._search_arbeitnow),
            ("Findwork", self._search_findwork),
            ("Himalayas", self._search_himalayas),
        ]
        
        for name, func in apis:
            try:
                jobs = func(query, location, num_results)
                if jobs:
                    print(f"✅ {name}: Found {len(jobs)} jobs")
                    all_jobs.extend(jobs)
            except Exception as e:
                print(f"⚠️ {name}: {e}")
        
        # Remove duplicates and return
        seen = set()
        unique = []
        for job in all_jobs:
            key = f"{job.title}|{job.company}".lower()
            if key not in seen:
                seen.add(key)
                unique.append(job)
        
        return unique[:num_results]
    
    def _search_remotive(self, query: str, location: str, num_results: int) -> List[FreeJobResult]:
        """
        Search Remotive.io - Free API for remote tech jobs.
        No API key required.
        """
        jobs = []
        
        # Map query to category
        category = self._get_remotive_category(query)
        
        url = "https://remotive.com/api/remote-jobs"
        params = {"limit": num_results}
        if category:
            params["category"] = category
        
        response = self.session.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        for job_data in data.get("jobs", [])[:num_results]:
            # Filter by query if provided
            title = job_data.get("title", "")
            company = job_data.get("company_name", "")
            description = job_data.get("description", "")
            
            # Relevance check - match ANY keyword from query
            if not self._matches_query(f"{title} {description}"):
                continue
            
            job = FreeJobResult(
                id=f"remotive_{job_data.get('id', '')}",
                title=title,
                company=company,
                location=job_data.get("candidate_required_location", "Remote"),
                description=self._clean_html(description)[:500],
                salary=job_data.get("salary", "Not specified") or "Not specified",
                apply_url=job_data.get("url", ""),
                source="remotive",
                posted_date=job_data.get("publication_date", ""),
                job_type=job_data.get("job_type", ""),
                required_skills=self._extract_skills(description)
            )
            jobs.append(job)
        
        return jobs
    
    def _search_arbeitnow(self, query: str, location: str, num_results: int) -> List[FreeJobResult]:
        """
        Search Arbeitnow - Free API for European + Remote jobs.
        No API key required.
        """
        jobs = []
        
        url = "https://www.arbeitnow.com/api/job-board-api"
        
        response = self.session.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        for job_data in data.get("data", [])[:num_results * 2]:
            title = job_data.get("title", "")
            description = job_data.get("description", "")
            
            # Filter by query - match ANY keyword
            if not self._matches_query(f"{title} {description}"):
                continue
            
            # Filter by location if provided
            job_location = job_data.get("location", "")
            if location and location.lower() not in job_location.lower():
                if "remote" not in job_location.lower():
                    continue
            
            job = FreeJobResult(
                id=f"arbeitnow_{job_data.get('slug', '')}",
                title=title,
                company=job_data.get("company_name", "Unknown"),
                location=job_location or "Remote",
                description=self._clean_html(description)[:500],
                salary="Not specified",
                apply_url=job_data.get("url", ""),
                source="arbeitnow",
                posted_date=job_data.get("created_at", ""),
                job_type="Remote" if job_data.get("remote", False) else "On-site",
                required_skills=job_data.get("tags", []) or self._extract_skills(description)
            )
            jobs.append(job)
            
            if len(jobs) >= num_results:
                break
        
        return jobs
    
    def _search_findwork(self, query: str, location: str, num_results: int) -> List[FreeJobResult]:
        """
        Search Findwork.dev - Free API for developer jobs.
        No API key required for basic access.
        """
        jobs = []
        
        url = "https://findwork.dev/api/jobs/"
        params = {
            "search": query,
            "location": location or "remote",
        }
        
        try:
            response = self.session.get(url, params=params, timeout=15)
            if response.status_code != 200:
                return []
            
            data = response.json()
            
            for job_data in data.get("results", [])[:num_results]:
                job = FreeJobResult(
                    id=f"findwork_{job_data.get('id', '')}",
                    title=job_data.get("role", "Unknown"),
                    company=job_data.get("company_name", "Unknown"),
                    location=job_data.get("location", "Remote"),
                    description=job_data.get("text", "")[:500],
                    salary="Not specified",
                    apply_url=job_data.get("url", ""),
                    source="findwork",
                    posted_date=job_data.get("date_posted", ""),
                    job_type=job_data.get("employment_type", ""),
                    required_skills=job_data.get("keywords", [])
                )
                jobs.append(job)
        except:
            pass
        
        return jobs
    
    def _search_himalayas(self, query: str, location: str, num_results: int) -> List[FreeJobResult]:
        """
        Search Himalayas.app - Free API for remote jobs.
        """
        jobs = []
        
        url = "https://himalayas.app/jobs/api"
        params = {"limit": num_results}
        
        try:
            response = self.session.get(url, params=params, timeout=15)
            if response.status_code != 200:
                return []
            
            data = response.json()
            
            for job_data in data.get("jobs", [])[:num_results * 2]:
                title = job_data.get("title", "")
                description = job_data.get("description", "")
                
                # Filter by query - match ANY keyword
                if not self._matches_query(f"{title} {description}"):
                    continue
                
                job = FreeJobResult(
                    id=f"himalayas_{job_data.get('id', '')}",
                    title=title,
                    company=job_data.get("companyName", "Unknown"),
                    location="Remote",
                    description=self._clean_html(description)[:500],
                    salary=self._format_salary(job_data.get("minSalary"), job_data.get("maxSalary")),
                    apply_url=job_data.get("applicationLink", "") or job_data.get("url", ""),
                    source="himalayas",
                    posted_date=job_data.get("pubDate", ""),
                    required_skills=job_data.get("categories", [])
                )
                jobs.append(job)
                
                if len(jobs) >= num_results:
                    break
        except:
            pass
        
        return jobs
    
    def _get_remotive_category(self, query: str) -> Optional[str]:
        """Map search query to Remotive category."""
        query_lower = query.lower()
        
        categories = {
            "software-dev": ["developer", "engineer", "programming", "software", "backend", "frontend", "full stack", "python", "java", "javascript"],
            "data": ["data", "machine learning", "ml", "ai", "analytics", "scientist"],
            "devops": ["devops", "sre", "infrastructure", "cloud", "aws", "kubernetes"],
            "design": ["designer", "ux", "ui", "product design"],
            "marketing": ["marketing", "seo", "growth"],
            "product": ["product manager", "product owner"],
        }
        
        for category, keywords in categories.items():
            if any(kw in query_lower for kw in keywords):
                return category
        
        return "software-dev"  # Default
    
    def _clean_html(self, html: str) -> str:
        """Remove HTML tags from text."""
        clean = re.sub(r'<[^>]+>', ' ', html)
        clean = re.sub(r'\s+', ' ', clean)
        return clean.strip()
    
    def _matches_query(self, text: str, min_matches: int = 1) -> bool:
        """Check if text matches ANY keyword from the search query."""
        if not hasattr(self, 'query_keywords') or not self.query_keywords:
            return True
        text_lower = text.lower()
        matches = sum(1 for kw in self.query_keywords if kw in text_lower)
        return matches >= min_matches
    
    def _format_salary(self, min_sal: Optional[int], max_sal: Optional[int]) -> str:
        """Format salary range."""
        if min_sal and max_sal:
            return f"${min_sal:,} - ${max_sal:,}"
        elif min_sal:
            return f"${min_sal:,}+"
        elif max_sal:
            return f"Up to ${max_sal:,}"
        return "Not specified"
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from text using resume skills (priority) + defaults."""
        found = []
        text_lower = text.lower()
        for skill in self.skill_keywords:
            if skill.lower() in text_lower:
                found.append(skill)
        return found[:10]


def search_free_jobs(query: str, location: str = "", num_results: int = 20, resume_skills: List[str] = None) -> List[Dict]:
    """
    Search free job APIs (no API key required).
    
    Args:
        query: Job search query
        location: Location filter  
        num_results: Number of results
        resume_skills: Skills from user's resume for better matching
        
    Returns:
        List of job dictionaries
    """
    api = FreeJobAPIs(resume_skills=resume_skills)
    jobs = api.search_all(query, location, num_results)
    return [j.to_dict() for j in jobs]
