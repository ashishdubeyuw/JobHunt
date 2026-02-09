"""
Test Suite for Job Matching Application
Run with: pytest tests/test_app.py -v
"""

import os
import sys
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestModuleImports:
    """Test that all modules import correctly."""
    
    def test_import_scrapers(self):
        from modules.scrapers import JobScraper, load_mock_jobs
        assert JobScraper is not None
        assert load_mock_jobs is not None
    
    def test_import_parsers(self):
        from modules.parsers import ResumeParser
        assert ResumeParser is not None
    
    def test_import_matching_engine(self):
        from modules.matching_engine import MatchingEngine, MatchResult
        assert MatchingEngine is not None
        assert MatchResult is not None
    
    def test_import_agents(self):
        from modules.agents import RecruiterAssistant, CoverLetterGenerator
        assert RecruiterAssistant is not None
        assert CoverLetterGenerator is not None
    
    def test_import_scheduler(self):
        from modules.scheduler import JobSearchScheduler, UserProfile
        assert JobSearchScheduler is not None
        assert UserProfile is not None
    
    def test_import_notifications(self):
        from modules.notifications import send_email_notification, send_whatsapp_notification
        assert send_email_notification is not None
        assert send_whatsapp_notification is not None


class TestMockDataLoading:
    """Test mock data loading functionality."""
    
    def test_load_mock_jobs(self):
        from modules.scrapers import load_mock_jobs
        jobs = load_mock_jobs()
        
        assert isinstance(jobs, list)
        assert len(jobs) > 0
    
    def test_mock_job_structure(self):
        from modules.scrapers import load_mock_jobs
        jobs = load_mock_jobs()
        
        required_fields = ["id", "title", "company", "location", "description"]
        
        for job in jobs:
            for field in required_fields:
                assert field in job, f"Missing required field: {field}"
    
    def test_mock_jobs_have_apply_url(self):
        from modules.scrapers import load_mock_jobs
        jobs = load_mock_jobs()
        
        for job in jobs:
            assert "apply_url" in job, f"Job {job.get('id')} missing apply_url"


class TestResumeParser:
    """Test resume parsing functionality."""
    
    def test_parser_initialization(self):
        from modules.parsers import ResumeParser
        parser = ResumeParser()
        
        assert parser is not None
        assert hasattr(parser, 'parse_pdf')
        assert hasattr(parser, 'extract_skills')
    
    def test_skill_extraction(self):
        from modules.parsers import ResumeParser
        parser = ResumeParser()
        
        test_text = """
        Senior Software Engineer with 5 years experience.
        Skills: Python, JavaScript, React, AWS, Docker, Kubernetes.
        Proficient in Machine Learning and TensorFlow.
        """
        
        skills = parser.extract_skills(test_text)
        
        assert "Python" in skills
        assert "JavaScript" in skills
        assert "AWS" in skills
    
    def test_experience_extraction(self):
        from modules.parsers import ResumeParser
        parser = ResumeParser()
        
        test_cases = [
            ("5+ years of experience in software development", 5),
            ("Experience: 3 years in data science", 3),
            ("10 years working with Python", 10),
        ]
        
        for text, expected in test_cases:
            years = parser.extract_experience_years(text)
            assert years == expected, f"Expected {expected}, got {years} for: {text}"
    
    def test_email_extraction(self):
        from modules.parsers import ResumeParser
        parser = ResumeParser()
        
        test_text = "Contact me at john.doe@example.com for more info."
        email = parser.extract_email(test_text)
        
        assert email == "john.doe@example.com"


class TestMatchingEngine:
    """Test the hybrid matching engine."""
    
    def test_engine_initialization(self):
        from modules.matching_engine import MatchingEngine
        engine = MatchingEngine()
        
        assert engine is not None
        assert engine.SKILLS_WEIGHT == 0.50
        assert engine.EXPERIENCE_WEIGHT == 0.30
        assert engine.SEMANTIC_WEIGHT == 0.20
    
    def test_skills_scoring(self):
        from modules.matching_engine import MatchingEngine
        engine = MatchingEngine()
        
        resume_skills = {"python", "javascript", "react"}
        job = {"required_skills": ["Python", "JavaScript", "React", "AWS"]}
        
        score = engine._calculate_skills_score(resume_skills, job)
        
        # 3 out of 4 skills match
        assert score >= 0.5, f"Expected score >= 0.5, got {score}"
    
    def test_experience_scoring(self):
        from modules.matching_engine import MatchingEngine
        engine = MatchingEngine()
        
        # Meeting requirements
        score = engine._calculate_experience_score(5, {"experience_years": 5})
        assert score == 1.0
        
        # Exceeding requirements
        score = engine._calculate_experience_score(10, {"experience_years": 5})
        assert score == 1.0
        
        # Below requirements
        score = engine._calculate_experience_score(2, {"experience_years": 5})
        assert score < 1.0
    
    def test_match_resume(self):
        from modules.matching_engine import MatchingEngine
        from modules.scrapers import load_mock_jobs
        
        engine = MatchingEngine()
        jobs = load_mock_jobs()
        engine.jobs = jobs
        
        resume_data = {
            "skills": ["Python", "Machine Learning", "TensorFlow"],
            "experience_years": 4,
            "raw_text": "Data scientist with ML experience"
        }
        
        matches = engine.match_resume(resume_data, top_k=5)
        
        assert len(matches) > 0
        assert len(matches) <= 5
        assert all(hasattr(m, 'final_score') for m in matches)
        
        # Verify sorted by score
        scores = [m.final_score for m in matches]
        assert scores == sorted(scores, reverse=True)


class TestJobScraper:
    """Test job scraper functionality."""
    
    def test_scraper_initialization(self):
        from modules.scrapers import JobScraper
        scraper = JobScraper()
        
        assert scraper is not None
    
    def test_scrape_without_api_key(self):
        from modules.scrapers import JobScraper
        scraper = JobScraper(api_key=None)
        
        jobs = scraper.scrape_jobs("software engineer", num_results=5)
        
        assert isinstance(jobs, list)
        # Should return mock data when no API key
        assert len(jobs) <= 5


class TestAgents:
    """Test LangChain agents."""
    
    def test_recruiter_assistant_init(self):
        from modules.agents import RecruiterAssistant
        assistant = RecruiterAssistant(api_key=None)
        
        assert assistant is not None
    
    def test_cover_letter_generator_init(self):
        from modules.agents import CoverLetterGenerator
        generator = CoverLetterGenerator(api_key=None)
        
        assert generator is not None
    
    def test_fallback_cover_letter(self):
        from modules.agents import CoverLetterGenerator
        generator = CoverLetterGenerator(api_key=None)
        
        job = {"title": "Engineer", "company": "TechCorp"}
        resume = {"skills": ["Python"], "experience_years": 3}
        
        letter = generator._fallback_cover_letter(job, resume)
        
        assert "TechCorp" in letter
        assert "Engineer" in letter


class TestScheduler:
    """Test scheduling functionality."""
    
    def test_scheduler_init(self):
        from modules.scheduler import JobSearchScheduler
        scheduler = JobSearchScheduler()
        
        assert scheduler is not None
    
    def test_user_profile(self):
        from modules.scheduler import UserProfile
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            profile = UserProfile("test_user", data_dir=Path(tmpdir))
            
            profile.set_notification_preferences(
                email="test@example.com",
                channel="email"
            )
            
            assert profile.data["email"] == "test@example.com"
            assert profile.data["notification_channel"] == "email"


class TestNotifications:
    """Test notification module."""
    
    def test_email_html_generation(self):
        from modules.notifications import _create_email_html
        
        jobs = [
            {
                "title": "Engineer",
                "company": "TechCorp",
                "location": "Remote",
                "salary": "$100k",
                "score": 0.85,
                "apply_url": "https://example.com"
            }
        ]
        
        html = _create_email_html(jobs)
        
        assert "Engineer" in html
        assert "TechCorp" in html
        assert "85%" in html
    
    def test_whatsapp_message_generation(self):
        from modules.notifications import _create_whatsapp_message
        
        jobs = [
            {
                "title": "Data Scientist",
                "company": "AI Corp",
                "location": "NYC",
                "salary": "$150k",
                "score": 0.90,
                "apply_url": "https://example.com"
            }
        ]
        
        message = _create_whatsapp_message(jobs)
        
        assert "Data Scientist" in message
        assert "AI Corp" in message
        assert "90%" in message


# Integration test
class TestIntegration:
    """Integration tests for the full workflow."""
    
    def test_full_matching_workflow(self):
        """Test complete resume-to-matches workflow."""
        from modules.scrapers import load_mock_jobs
        from modules.parsers import ResumeParser
        from modules.matching_engine import MatchingEngine
        
        # 1. Load jobs
        jobs = load_mock_jobs()
        assert len(jobs) > 0
        
        # 2. Create matching engine
        engine = MatchingEngine()
        engine.jobs = jobs
        
        # 3. Simulate resume data
        resume_data = {
            "skills": ["Python", "SQL", "Machine Learning", "TensorFlow"],
            "experience_years": 3,
            "raw_text": "Experienced data scientist with strong ML background.",
            "summary": "Data scientist with 3 years experience in ML"
        }
        
        # 4. Match
        matches = engine.match_resume(resume_data, top_k=3)
        
        # Verify results
        assert len(matches) == 3
        assert all(m.final_score > 0 for m in matches)
        
        # Data scientist job should rank well
        job_titles = [m.job.get("title", "").lower() for m in matches]
        assert any("data" in title for title in job_titles), "Expected data-related job in top matches"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
